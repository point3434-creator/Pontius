"""Literal arithmetic and adverse retained-record controls; no measured workloads."""
import base64
import copy
import hashlib
import importlib.util
import json
from pathlib import Path, PureWindowsPath
import tempfile
import unittest

SPEC = importlib.util.spec_from_file_location(
    'workload_report',
    Path(__file__).resolve().parents[1] / 'tools/v0a_blueprint_workload_report.py')
report = importlib.util.module_from_spec(SPEC)
if SPEC.origin and Path(SPEC.origin).exists():
    SPEC.loader.exec_module(report)


class ReportControls(unittest.TestCase):
    def test_closed_observations_reject_corruption_and_incomplete_counts(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            full_run(root, 'completed_capture')
            with self.assertRaises(ValueError):
                report.read_run(root)
        cell = control_plan()['cells'][0]
        valid = construction_observation()
        valid['memory_samples'] = [
            {'pid': 7, 'ns': i, 'stage': stage, 'private_commit': 5, 'working_set': 4,
             'peak_private_commit': 6, 'peak_working_set': 7}
            for i, stage in enumerate(('ready', 'periodic', 'final'))]
        report.validate_observations(valid, cell)
        for key, value in (('prepare_ns', True), ('source_sha256', 'x'), ('extra', 0),
                           ('wire_bytes', -1), ('memory_samples', [{'pid': 1}]),
                           ('memory_samples', []), ('memory_samples', memory_samples()[1:])):
            malformed = dict(valid, **{key: value})
            with self.subTest(key=key), self.assertRaises(ValueError):
                report.validate_observations(malformed, cell)
        cell.update(kind='history', parameters=history_parameters())
        obs = history_observation(1_000_000)
        report.validate_observations(obs, cell)
        obs['blocks'][0]['miss']['individual_ns'].pop()
        with self.assertRaises(ValueError):
            report.validate_observations(obs, cell)

    def test_summary_seven_rule_names_and_independent_runtime_observations(self):
        plan = control_plan()
        plan['cells'] = []
        second = dict(plan['runtimes'][0], id='3.14', version='3.14.6')
        plan['runtimes'].append(second)
        records = []
        for runtime, cost in (('3.11', 1_000_000), ('3.14', 999_999)):
            ident = 'h' + runtime.replace('.', '')
            plan['cells'].append({'id': ident, 'runtime': runtime, 'kind': 'history', 'size': 8191,
                                  'parameters': history_parameters(), 'argv': ['D:/python.exe']})
            records.append(completed_result(ident, history_observation(cost)))
        summary = report.summarize(records, plan)
        rules = summary['runtimes']['3.11']['rules']
        self.assertEqual(set(rules), {'response_margin', 'interface_cap', 'dominant_session_phase',
                                     'useful_preparation_reuse', 'material_miss_path',
                                     'excess_scaling', 'current_process_resource_concern'})
        self.assertTrue(rules['material_miss_path']['triggered'])
        self.assertFalse(summary['runtimes']['3.14']['rules']['material_miss_path']['triggered'])
        self.assertEqual(rules['material_miss_path']['case_ids'], ['h311'])
        self.assertFalse(summary['clean'])
        other = dict(plan['cells'][1], id='h314missing')
        other['parameters'] = dict(other['parameters'], bin='31-33')
        plan['cells'].append(other)
        record = dict(control_result('h314missing', 'interrupted'), cause='budget_exhausted')
        records.append(record)
        result = report.summarize(records, plan)['runtimes']['3.14']
        self.assertIsNone(result['rules']['material_miss_path']['triggered'])
        self.assertEqual(result['rules']['material_miss_path']['incomplete_case_ids'],
                         ['h314missing'])
        self.assertEqual(result['retained_results'][-1], record)

    def test_profiled_parent_and_child_traffic_stay_separate(self):
        for version in (1, 2):
            record, cell, reference, retained = completed_schema_fixture(report, version)
            report.admit_completed_session(record, cell, reference, set(), retained.__getitem__)
            corrupted = copy.deepcopy(record)
            corrupted['observations']['actions'][0]['elapsed_ns'] += 1
            with self.assertRaises(ValueError):
                report.admit_completed_session(
                    corrupted, cell, reference, set(), retained.__getitem__)
            for change in ('status', 'accounting_complete', 'failure_reason'):
                raw_name = 'cells/' + cell['id'] + '/stdout.bin'
                outer = json.loads(retained[raw_name])
                hand = outer['hands'][0]['result']
                frames = [json.loads(line) for line in base64.b64decode(
                    hand['child_stdout_base64']).splitlines()]
                frames[-1][change] = {'status': 'failed', 'accounting_complete': False,
                                     'failure_reason': 'trace_invalid'}[change]
                hand['child_stdout_base64'] = base64.b64encode(
                    b''.join(encoded(frame) for frame in frames)).decode()
                changed = dict(retained, **{raw_name: encoded(outer)})
                with self.subTest(closure=change), self.assertRaises(ValueError):
                    report.admit_completed_session(record, cell, reference, set(),
                                                   changed.__getitem__)
        plan = control_plan()
        plan['cells'] = []
        records = []
        for index, diagnostic in enumerate((False, True)):
            ident = 's' + str(index)
            cell = {'id': ident, 'runtime': '3.11', 'kind': 'session', 'size': 8191,
                    'parameters': {'diagnostic': diagnostic, 'ordinal': 0, 'deal': 0, 'seat': 3,
                                   'lineup': 0, 'strategy': 'blueprint-v1', 'session_id': ident,
                                   'session_path': 'D:/s.json', 'blueprint_path': 'D:/b.json'},
                    'argv': ['D:/python.exe']}
            plan['cells'].append(cell)
            obs = {'raw_events': [], 'actions': [
                {'id': ident + '-a1', 'hand_id': 'h', 'event_index': 0, 'action_index': 1,
                 'street': 'preflop', 'history_atoms': 0, 'hit': False, 'first': True,
                 'elapsed_ns': 900 if diagnostic else 100, 'compute_ns': 0,
                 'uninstrumented_ns': 900 if diagnostic else 100, 'work_cutoff': False,
                 'deadline': False, 'fallback_used': True, 'selection_origin': 'blueprint'}],
                   'preparation': [{'hand_id': 'h', 'preparation_compute_seconds': 0.0,
                       'post_terminal_compute_seconds': 0.0, 'accounting_complete': True,
                       'interrupted_response_count': 0}],
                   'session_status': 'completed', 'settlement': {},
                   'reference_id': 'ref'}
            if diagnostic:
                obs['raw_events'] = [{'event': 'call', 'point': 'session:Session.run', 'ns': 0},
                                     {'event': 'return', 'point': 'session:Session.run',
                                      'ns': 1000}]
            records.append(dict(completed_result(ident, obs), outer_ns=1000))
        # Whole missing span pairs must not become valid orchestration time.
        with self.assertRaisesRegex(ValueError, 'applicable'):
            report.summarize(records, plan)
        records[1]['observations']['raw_events'] = complete_profile()
        result = report.summarize(records, plan)['runtimes']['3.11']
        self.assertEqual(result['traffic']['natural']['raw'], [100])
        self.assertEqual(sum(result['profile_cases'][0]['phases'].values()), 1000)
        for point in {row['point'] for row in complete_profile()} - {'session:Session.run'}:
            broken = [row for row in complete_profile() if row['point'] != point]
            with self.subTest(point=point), self.assertRaises(ValueError):
                report.session_profile(broken, 1000, 'blueprint-v1')
        for point in ('session:Session.validate', 'session:Admission.check', 'host:Source.check',
                      'host:OwnedInput.check', 'session:Schedule.derive'):
            events = complete_profile()
            begin = next(i for i, e in enumerate(events) if e['point'] == point)
            end = next(i for i in range(begin + 1, len(events))
                       if events[i]['point'] == point and events[i]['event'] == 'return')
            broken = [e for i, e in enumerate(events) if i not in (begin, end)]
            with self.subTest(missing_occurrence=point), self.assertRaises(ValueError):
                report.session_profile(broken, 1000, 'blueprint-v1')
        with self.assertRaises(ValueError):
            report.session_profile(complete_profile(), 1000, 'baseline-rules-v1')
        self.assertTrue(report.session_profile(complete_profile(True), 1000, 'baseline-rules-v1'))
        self.assertEqual(result['parent_wall']['raw'], [1000])
        plan['cells'][0]['parameters']['strategy'] = 'baseline-rules-v1'
        records[0]['observations']['actions'][0].update(
            hit=True, fallback_used=False, selection_origin='provider')
        traffic = report.summarize(records[:1], dict(plan, cells=plan['cells'][:1]))[
            'runtimes']['3.11']['traffic']
        self.assertTrue(traffic['raw'][0]['membership'])
        self.assertIsNone(traffic['strata'][0]['hit'])
        self.assertEqual(traffic['strata'][0]['selection_origin'], 'provider')
        for change in ('session_status', 'preparation', 'action_identity'):
            changed = json.loads(json.dumps(records[0]['observations']))
            if change == 'session_status':
                changed['session_status'] = 'failed'
            elif change == 'preparation':
                changed['preparation'][0]['accounting_complete'] = False
            else:
                changed['actions'][0]['action_index'] = 0
            with self.subTest(change=change), self.assertRaises(ValueError):
                report.validate_observations(changed, plan['cells'][0])

    def test_census_preserves_missing_failed_and_unattempted(self):
        plan = control_plan()
        records = [control_result('c0', 'failed'), control_result('c1', 'unattempted')]
        summary = report.summarize(records, plan)
        self.assertFalse(summary['clean'])
        self.assertEqual(summary['census']['failed'], ['c0'])
        self.assertEqual(summary['census']['unattempted'], ['c1'])
        self.assertEqual(summary['census']['missing'], ['c2'])
        self.assertEqual(summary['planned'], ['c0', 'c1', 'c2'])
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            full_run(root, 'final_refusal')
            with self.assertRaisesRegex(ValueError, 'retention'):
                report.read_run(root)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            full_run(root, 'worker_frame')
            with self.assertRaises(ValueError):
                report.read_run(root)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            full_run(root, 'duplicate_ready')
            failed = report.read_run(root)
            self.assertEqual(failed['summary']['run_status'], 'failed')
            self.assertEqual(failed['summary']['census']['failed'],
                             [failed['plan']['cells'][0]['id']])
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            full_run(root, 'retention')
            retained = report.read_run(root)['summary']
            self.assertTrue(retained.get('retention_failures'),
                            'original run retention failure disappeared')
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            full_run(root, 'failed_safety')
            retained = report.read_run(root)['summary']['runtimes']['3.11']
            self.assertEqual(retained['traffic']['natural']['n'], 0)
            self.assertTrue(retained['rules']['response_margin']['contract_failure'],
                            'original failed capture deadline disappeared')

    def test_census_rejects_duplicates_unknown_cells_and_wrong_types(self):
        contained = dict(control_result('c0', 'failed'), cause='containment_failed')
        report.validate_result(contained)
        report.validate_result(dict(control_result('c0', 'interrupted'), cause='interrupted'))
        for records in ([control_result('alien')], [control_result('c0')] * 2):
            with self.assertRaises(ValueError):
                report.summarize(records, control_plan())
        for mutate in ('cell', 'runtime', 'version', 'bool', 'result'):
            plan, records = control_plan(), [control_result('c0')]
            if mutate == 'cell':
                plan['cells'].append(plan['cells'][0])
            elif mutate == 'runtime':
                plan['cells'][0]['runtime'] = 'unknown'
            elif mutate == 'version':
                plan['version'] = 'foreign'
            elif mutate == 'bool':
                plan['cells'][0]['size'] = True
            else:
                records[0]['outer_ns'] = True
            with self.subTest(mutate=mutate), self.assertRaises(ValueError):
                report.summarize(records, plan)
        for value in (True, -1, 5, 1.0):
            plan = control_plan()
            plan['cells'][0]['parameters']['observation'] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                report.summarize([], plan)
        for field in ('status', 'cause'):
            malformed = control_result('c0')
            malformed[field] = []
            with self.subTest(field=field), self.assertRaises(ValueError):
                report.summarize([malformed], control_plan())
        malformed = control_result('c0')
        malformed['secondary'] = [[]]
        with self.assertRaises(ValueError):
            report.summarize([malformed], control_plan())

    def test_manifest_identity_census_and_read_is_nonmutating(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            full_run(root, 'authority')
            with self.assertRaises(ValueError):
                report.read_run(root)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            populate_run(root)
            # A self-consistent three-cell/one-runtime file set is not the fixed public run.
            with self.assertRaisesRegex(ValueError, 'schedule|runtime|qualification'):
                report.read_run(root)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            full_run(root)
            before = {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob('*')
                      if p.is_file()}
            loaded = report.read_run(root)
            self.assertEqual(len(loaded['summary']['census']['unattempted']), 340)
            self.assertEqual(loaded['query_traffic']['count'], 1152)
            for fit in (0, 128, 1024, 8192, 9000, 65536):
                synthetic = dict(loaded['plan'], cells=fixture_schedule(
                    loaded['plan']['runtimes'], fit))
                report.admit_schedule(synthetic, fit)
            self.assertEqual(before, {p.relative_to(root).as_posix(): p.read_bytes()
                                      for p in root.rglob('*') if p.is_file()})
            (root / 'extra').write_bytes(b'x')
            with self.assertRaises(ValueError):
                report.read_run(root)
            (root / 'extra').unlink()
            (root / 'terminal.json').write_bytes(b'{}\n')
            with self.assertRaises(ValueError):
                report.read_run(root)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            full_run(root)
            loaded = report.read_run(root)
            clocks = loaded['runtime_clocks']['3.11']
            self.assertTrue(clocks['available'])
            self.assertEqual(clocks['clocks']['monotonic']['implementation'], 'GetTickCount64()')
            self.assertEqual(clocks['clocks']['monotonic']['resolution'], 0.015625)
            self.assertEqual(clocks['clocks']['perf_counter']['resolution'], 1e-7)
            self.assertIn('resolution-limited', clocks['caveat'])
            self.assertIn('history', clocks['caveat'].lower())
            self.assertEqual(report.distribution([0])['raw'], [0])

    def test_manifest_rejects_escape_alias_missing_and_terminal_mismatch(self):
        for defect in ('short_runtime', 'short_cell', 'argv', 'environment', 'qualification',
                       'capture', 'observations', 'supervision', 'context', 'natural_missing',
                       'natural_membership'):
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                full_run(root, defect)
                with self.subTest(defect=defect), self.assertRaises(ValueError):
                    report.read_run(root)
        for defect in ('escape', 'alias', 'missing', 'terminal', 'population', 'intent',
                       'intent_type', 'environment'):
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                populate_run(root, defect)
                with self.subTest(defect=defect), self.assertRaises(ValueError):
                    report.read_run(root)

    def test_json_duplicate_keys_and_nonfinite_refuse(self):
        for defect in ('grant', 'grant_missing', 'claim', 'qualification_grant',
                       'qualification_records', 'qualification_missing', 'probe_stderr'):
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                full_run(root, defect)
                with self.subTest(defect=defect), self.assertRaises(ValueError):
                    report.read_run(root)
        for raw in (b'{"a":1,"a":2}', b'[NaN]', b'[Infinity]', b'[1e999]', b'{}\r\n'):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                report.parse_json(raw)

    def test_json_size_depth_and_exact_types(self):
        self.assertEqual(report.parse_json(b'{"a":[1,true,null]}\n'), {'a': [1, True, None]})
        with self.assertRaises(ValueError):
            report.parse_json(b'[' * 65 + b'0' + b']' * 65)
        with self.assertRaises(ValueError):
            report.parse_json(b'{}', limit=1)
        for value in (True, -1, 1.0):
            with self.assertRaises(ValueError):
                report.distribution([value])

    def test_nearest_rank_minimum_counts_and_raw_denominator(self):
        small = report.distribution(list(range(1, 20)))
        self.assertEqual((small['n'], small['maximum'], small['p95'], small['p99']),
                         (19, 19, None, None))
        self.assertEqual(report.distribution(list(range(1, 21)))['p95'], 19)
        self.assertIsNone(report.distribution(list(range(1, 1000)))['p99'])
        self.assertEqual(report.distribution(list(range(1, 1001)))['p99'], 990)
        self.assertEqual(report.distribution([])['median'], None)

    def test_exclusive_spans_nested_and_constructor_precedence(self):
        events = [
            {'event': 'call', 'point': 'session:Session.run', 'ns': 10},
            {'event': 'call', 'point': 'session:Admission.__init__', 'ns': 20},
            {'event': 'call', 'point': 'host:Source.check', 'ns': 30},
            {'event': 'return', 'point': 'host:Source.check', 'ns': 50},
            {'event': 'return', 'point': 'session:Admission.__init__', 'ns': 70},
            {'event': 'call', 'point': 'host:WireConsumer.exchange', 'ns': 80},
            {'event': 'call', 'point': 'host:WireConsumer.decision', 'ns': 90},
            {'event': 'return', 'point': 'host:WireConsumer.decision', 'ns': 100},
            {'event': 'return', 'point': 'host:WireConsumer.exchange', 'ns': 110},
            {'event': 'return', 'point': 'session:Session.run', 'ns': 120}]
        result = report.reduce_spans(events, 150)
        self.assertEqual(result['phases']['setup_admission'], 50)
        self.assertEqual(result['phases']['source_validation'], 0)
        self.assertEqual(result['phases']['exchange_wait'], 20)
        self.assertEqual(result['phases']['reference_validation'], 10)
        self.assertEqual(result['phases']['orchestration'], 30)
        self.assertEqual(result['phases']['residual'], 40)
        self.assertEqual(sum(result['phases'].values()), 150)

    def test_invalid_spans_never_guess_durations(self):
        call = {'event': 'call', 'point': 'session:Session.run', 'ns': 0}
        close = {'event': 'return', 'point': 'session:Session.run', 'ns': 10}
        invalid = [[], [call], [close, call], [call, close, call, close],
                   [call, dict(close, ns=-1)], [call, dict(close, ns=True)],
                   [call, dict(close, point='host:MadeUp.check')],
                   [call, dict(close, point='host:Source.check')]]
        for events in invalid:
            with self.subTest(events=events), self.assertRaises(ValueError):
                report.reduce_spans(events, 20)

    def test_phase_dominance_two_cases_and_inflation_boundary(self):
        cases = [{'id': str(i), 'outer_ns': 200_000_000, 'unprofiled_ns': 160_000_000,
                  'phases': {'setup_admission': 100_000_000, 'residual': 100_000_000}}
                 for i in range(2)]
        self.assertEqual(report.phase_dominance(cases)['triggered'], ['setup_admission'])
        cases[1]['outer_ns'] += 1
        cases[1]['phases']['residual'] += 1
        self.assertEqual(report.phase_dominance(cases)['triggered'], [])
        self.assertFalse(report.phase_dominance(cases)['cases'][1]['eligible'])

    def test_reuse_exact_threshold_and_all_four_positive(self):
        fresh = [400_000_000] * 4
        retained = [320_000_000] * 4
        self.assertTrue(report.reuse(fresh, retained, 8)['triggered'])
        self.assertFalse(report.reuse(fresh, [320_000_001] * 4, 8)['triggered'])
        self.assertFalse(report.reuse(fresh, [0, 0, 0, 400_000_000], 8)['triggered'])
        self.assertIsNone(report.reuse(fresh[:3], retained[:3], 8)['triggered'])
        self.assertIsNone(report.reuse(fresh, retained, 1)['triggered'])
        plan = control_plan()
        plan['cells'] = [{'id': arm, 'runtime': '3.11', 'kind': 'reuse', 'size': 8191,
                          'parameters': {'hands': 8, 'repetition': 0, 'arm': arm,
                                         'trajectory_ordinals': list(range(8))},
                          'argv': ['D:/python.exe']} for arm in ('fresh', 'retained')]
        records = [completed_result(arm, {'memory_samples': memory_samples(), 'group_ns': 100,
                   'prepare_ns': [1] * (8 if arm == 'fresh' else 1),
                   'hash_ns': [] if arm == 'fresh' else [1] * 8, 'read_ns': 1, 'decode_ns': 1,
                   'query_count': 1, 'distinct_keys': 1, 'context_ids': [arm]})
                   for arm in ('fresh', 'retained')]
        with self.assertRaises(ValueError):
            report.summarize(records, plan)

    def test_miss_threshold_timer_sensitivity_and_batch_primacy(self):
        result = report.miss_path([1_000_000] * 20, [100_000_000], [50_000], [500_000])
        self.assertTrue(result['triggered'])
        self.assertTrue(result['key_priority'])
        self.assertEqual(result['primary'], 'batch_mean_ns')
        self.assertEqual(result['batch_mean_ns']['median'], 1_000_000)
        result = report.miss_path([1_000_000] * 20, [100_000_000], [50_001], [500_000])
        self.assertTrue(result['instrumentation_sensitive'])
        self.assertIsNone(result['triggered'])
        self.assertFalse(report.miss_path([999_999] * 20, [100], [0], [0])['triggered'])

    def test_byte_adjusted_scaling_fixed_anchors_and_sorting_proxy(self):
        census = {street: {name: [] for name in ('0', '3-5', '7-9', '15-17', '31-33', 'other')}
                  for street in ('preflop', 'flop', 'turn', 'river')}
        census['preflop']['0'] = [10, 20]
        metadata = {'size': 2, 'source_sha256': 'a' * 64, 'canonical_bytes': 40,
                    'key_bytes': 25, 'wire_bytes': 38, 'root_bytes': 7, 'row_bytes': 30,
                    'comma_bytes': 1, 'row_census': census}
        rows = report.artifact_report(metadata)
        self.assertEqual(rows['row_census']['preflop']['0']['mean'], 15)
        self.assertEqual(rows['row_census']['preflop']['0']['p95'], 20)
        self.assertEqual(rows['wire_bytes'], 38)
        with self.assertRaises(ValueError):
            report.artifact_report(dict(metadata, wire_bytes=39))
        samples = {0: [10] * 5, 1024: [110] * 5, 8192: [1010] * 5, 65536: [2011] * 5}
        work = {0: 20, 1024: 120, 8192: 820, 65536: 1620}
        result = report.scaling(samples, work, 'prepare')
        self.assertEqual(result[8192]['linear'], 810)
        self.assertEqual(result[8192]['ratio'], 1.25)
        self.assertFalse(result[8192]['triggered'])
        self.assertEqual(result[8192]['sorting'], 1050)
        self.assertTrue(result[65536]['triggered'])
        self.assertFalse(result[65536]['sorting_excess'])

    def test_scaling_nonpositive_and_thirty_percent_noise(self):
        work = {0: 0, 1024: 100, 8192: 800}
        samples = {0: [10] * 5, 1024: [10] * 5, 8192: [100] * 5}
        self.assertIsNone(report.scaling(samples, work, 'hash')[8192]['triggered'])
        samples[1024] = [100] * 5
        samples[8192] = [850, 1000, 1000, 1000, 1150]
        self.assertIsNotNone(report.scaling(samples, work, 'hash')[8192]['triggered'])
        samples[8192][-1] += 1
        self.assertIsNone(report.scaling(samples, work, 'hash')[8192]['triggered'])

    def test_response_cap_and_memory_adjacent_thresholds(self):
        self.assertTrue(hasattr(report, 'failed_session_facts'), 'failed safety reader absent')
        for version in (1, 2):
            fixture = failed_fixture(report, version=version)
            raw, child = packed(fixture)
            facts = report.failed_session_facts(raw, fixture['cell'], fixture['reference'])
            self.assertTrue(facts['complete'])
            self.assertEqual(len(facts['facts']), 1)
            limited = copy.deepcopy(fixture)
            limited['outer']['secondary_failures'] = ['host_limit']
            limited_facts = report.failed_session_facts(
                packed(limited)[0], fixture['cell'], fixture['reference'])
            self.assertEqual(len(limited_facts['facts']), 1)
            fact = facts['facts'][0]
            self.assertEqual(hashlib.sha256(child[fact['offset']:
                fact['offset'] + fact['bytes']]).hexdigest(), fact['sha256'])
            for name, raw, count, complete in counterexamples(fixture):
                with self.subTest(version=version, defect=name):
                    observed = report.failed_session_facts(
                        raw, fixture['cell'], fixture['reference'])
                    self.assertEqual(len(observed['facts']), count)
                    self.assertIs(observed['complete'], complete)
            cell = fixture['cell']
            cell['parameters'].update(diagnostic=False, ordinal=0, deal=0, lineup=0,
                                      session_path='D:/s.json', blueprint_path='D:/b.json')
            cell['argv'] = ['D:/python.exe']
            plan = dict(control_plan(), cells=[cell])
            record = dict(control_result(cell['id'], 'failed'), failed_session_facts=facts)
            observed = report.summarize([record], plan)
            runtime = observed['runtimes']['3.11']
            self.assertEqual(runtime['traffic']['natural']['n'], 0)
            self.assertEqual(observed['census']['failed'], [cell['id']])
            self.assertTrue(runtime['rules']['response_margin']['contract_failure'])
            self.assertTrue(runtime['rules']['response_margin']['triggered'])
            self.assertIn('response_margin', runtime['unresolved'])
        fixture = failed_fixture(report, elapsed=15_000_000_000)
        facts = report.failed_session_facts(packed(fixture)[0],
                                             fixture['cell'], fixture['reference'])
        self.assertFalse(facts['facts'][0]['record']['failure']['timing']['deadline_crossed'])
        timing = fixture['rows'][2]['failure']['timing']
        timing.update(status='interrupted', interruption_reason='clock_invalid',
            emission_observed_ns=None, elapsed_ns=None, response_compute_seconds=None,
            response_uninstrumented_seconds=None, deadline_crossed=None)
        fixture['rows'][2]['failure']['code'] = 'clock_invalid'
        facts = report.failed_session_facts(packed(fixture)[0],
                                             fixture['cell'], fixture['reference'])
        self.assertIsNone(facts['facts'][0]['record']['failure']['timing']['elapsed_ns'])
        actions = [{'id': 'a', 'seat': 3, 'first': True, 'size': 8191,
                    'elapsed_ns': 1_400_000_000, 'compute_ns': 100,
                    'uninstrumented_ns': 1_399_999_900, 'work_cutoff': False,
                    'deadline': False, 'street': 'preflop', 'history_atoms': 0,
                    'hit': False, 'strategy': 'blueprint-v1', 'trial_id': 't'}]
        result = report.response_safety(actions, 8191)
        self.assertTrue(result['triggered'])
        self.assertEqual(result['actions'][0]['work_margin_ns'], 12_600_000_000)
        actions[0]['compute_ns'] += 3
        rounded = report.response_safety(actions, 8191)
        self.assertEqual(rounded['actions'][0]['component_rounding_delta_ns'], -3)
        actions[0]['compute_ns'] += 1
        with self.assertRaises(ValueError):
            report.response_safety(actions, 8191)
        actions[0]['compute_ns'] -= 4
        actions[0]['elapsed_ns'] -= 1
        actions[0]['uninstrumented_ns'] -= 1
        self.assertFalse(report.response_safety(actions, 8191)['triggered'])
        actions[0]['seat'] = 0
        actions[0]['elapsed_ns'] = 2_000_000_000
        actions[0]['uninstrumented_ns'] = 1_999_999_900
        self.assertIsNone(report.response_safety(actions, 8191)['triggered'])
        actions[0]['deadline'] = True
        self.assertTrue(report.response_safety(actions, 8191)['triggered'])
        self.assertTrue(report.capacity(8191)['triggered'])
        self.assertFalse(report.capacity(8192)['triggered'])
        self.assertEqual(report.capacity(4096)['retained_fraction'], .5)
        self.assertTrue(report.resource_concern([536_870_912])['triggered'])
        self.assertFalse(report.resource_concern([536_870_911])['triggered'])
        self.assertIsNone(report.resource_concern([])['triggered'])

    def test_action_traffic_strata_never_double_count_or_pool_versions(self):
        # Full-query membership is a separate census, with IDs absent from CLI traffic.
        natural = [dict(id='r002-query-0000-000', trajectory_id='r002-query-0000',
                        hit=True, street='preflop', history_atoms=0),
                   dict(id='r002-query-0001-001', trajectory_id='r002-query-0001',
                        hit=False, street='turn', history_atoms=12)]
        self.assertTrue(hasattr(report, 'query_traffic'), 'full-query census reader is absent')
        query = report.query_traffic(natural)
        self.assertEqual((query['count'], query['hits'], query['misses']), (2, 1, 1))
        self.assertEqual(query['other_count'], 1)
        self.assertEqual(query['raw'], natural)
        with self.assertRaises(ValueError):
            report.query_traffic(natural + natural[:1])
        actions = [{'id': 'a' + str(i), 'seat': 3, 'first': i == 0, 'size': 5,
                    'elapsed_ns': n, 'compute_ns': 0, 'uninstrumented_ns': n,
                    'work_cutoff': False, 'deadline': False, 'street': 'preflop',
                    'history_atoms': 0, 'hit': i == 0, 'strategy': 'blueprint-v1',
                    'trial_id': 't'} for i, n in enumerate((10, 20, 90))]
        result = report.action_traffic(actions)
        self.assertEqual(result['natural']['median'], 20)
        self.assertEqual(result['natural']['n'], 3)
        self.assertEqual(result['case_ids'], ['a0', 'a1', 'a2'])
        self.assertEqual(sorted(row['distribution']['n'] for row in result['strata']), [1, 2])
        with self.assertRaises(ValueError):
            report.action_traffic(actions + actions[:1])


def complete_profile(baseline=False):
    # Literal successful-path topology from unchanged Session.run/prepare/play_hand.
    events = []
    def pair(point, nested=()):
        events.append(dict(event='call', point=point, ns=len(events)))
        for child in nested:
            pair(*child)
        events.append(dict(event='return', point=point, ns=len(events)))
    check = ('session:Admission.check', [('host:Source.check',)])
    validate = ('session:Session.validate', [check, ('host:OwnedInput.check',),
                                            ('host:OwnedInput.check',)])
    pair('session:Session.run', [
        ('session:Session.prepare', [('session:Admission.__init__', [
            ('session:Admission.check',), ('host:Source.__init__', [('host:Source.check',)]),
            ('host:Source.check',), check]), ('session:Schedule.derive',)]),
        ('session:Session.play_hand', [validate, ('session:Schedule.derive',),
            ('host:ChildConnection.__init__', [('host:ChildConnection.send',)]),
            ('host:WireConsumer.ready', [('host:ChildConnection.receive',)]),
            ('host:Table.start_event',), ('host:WireConsumer.exchange', [
                ('host:ChildConnection.send',), ('host:ChildConnection.receive',),
                ('host:ChildConnection.receive',), ('host:WireConsumer.decision',),
                *([('host:WireConsumer.provider_expected',)] if baseline else [])]),
            ('host:Table.next_event',), ('host:WireConsumer.complete', [
                ('host:ChildConnection.receive',), ('host:ChildConnection.receive',),
                ('host:ChildConnection.receive',), ('host:WireConsumer.settlement',)]),
            validate, ('host:ChildConnection.finish',), validate]), validate])
    return events


def control_plan():
    runtime = {'id': '3.11', 'version': '3.11.15', 'executable': 'D:/python.exe',
               'executable_sha256': '1' * 64, 'resolved_executable': 'D:/python-real.exe',
               'resolved_executable_sha256': '2' * 64, 'source_root': 'D:/source',
               'run_root': 'D:/run', 'source_sha256': '3' * 64, 'protocol_sha256': '4' * 64,
               'authorization': 'D:/authority.json'}
    return {'version': 'workload-r002-plan-v1', 'population_sha256': '5' * 64,
            'runtimes': [runtime], 'cells': [
                {'id': 'c' + str(i), 'runtime': '3.11', 'kind': 'construction', 'size': 0,
                 'parameters': {'observation': i}, 'argv': ['D:/python.exe', '-B', '-P']}
                for i in range(3)]}


def control_result(cell_id, status='unattempted'):
    return {'version': 'workload-r002-result-v1', 'cell_id': cell_id, 'status': status,
            'cause': 'worker_failed' if status == 'failed' else 'budget_exhausted',
            'secondary': [], 'observations': {}, 'files': [], 'outer_ns': None,
            'exit_code': None, 'cleanup': {'verified': False, 'active': None},
            'captures': {'stdout': None, 'stderr': None, 'truncated': False}}


def completed_result(ident, observation):
    return dict(control_result(ident), status='completed', cause=None, exit_code=0,
                outer_ns=1_000_000_000, observations=observation,
                cleanup={'verified': True, 'active': 0})


def construction_observation():
    return {'memory_samples': memory_samples(), 'source_sha256': 'a' * 64,
            'read_ns': 1, 'decode_ns': 2,
            'prepare_ns': 3, 'first_ns': 4, 'outer_total_ns': 10, 'canonical_ns': 5,
            'sha_ns': 6, 'wire_bytes': 10, 'key_bytes': 20, 'canonical_bytes': 30}


def history_parameters():
    return {'bin': '0', 'operation': 'provider', 'blocks': 5,
            'subblocks': ['hit', 'miss', 'miss', 'hit'], 'warmups': 10, 'batches': 10,
            'batch_calls': 100, 'individual_calls': 1000, 'empty_brackets': 10000,
            'empty_batches': 5, 'loop_batches': 5}


def history_observation(cost):
    return {'memory_samples': memory_samples(),
            'clock': {'implementation': 'control', 'monotonic': True,
                                          'adjustable': False, 'resolution': 1e-9},
            'empty_brackets_ns': [0] * 10000, 'empty_batches_ns': [0] * 5,
            'loop_batches_ns': [0] * 5,
            'blocks': [{'hit': {'context_ids': [], 'batch_ns': [], 'individual_ns': []},
                        'miss': {'context_ids': ['q0'], 'batch_ns': [cost * 100] * 20,
                                 'individual_ns': [cost] * 2000}} for _ in range(5)]}


def memory_samples(kind='construction'):
    stages = ('ready', 'idle', 'read', 'decode', 'prepare', 'first', 'final') \
        if kind == 'memory_untraced' else ('ready', 'periodic', 'final')
    return [{'pid': 7, 'ns': i, 'stage': stage, 'private_commit': 5, 'working_set': 4,
             'peak_private_commit': 6, 'peak_working_set': 7} for i, stage in enumerate(stages)]


def fixture_schedule(runtimes, fit=3):
    """Fixed arithmetic/schema fixture; no population or workload code is imported."""
    cells = []
    reuse_ids = [d * 72 + s * 12 + d % 3 * 2 + d % 2
                 for d in range(16) for s in (d % 6, (d + 3) % 6)]
    for r in runtimes:
        full = r['id'] == '3.11'
        source, run = PureWindowsPath(r['source_root']), PureWindowsPath(r['run_root'])
        specifications = []
        def construction(sizes):
            specifications.extend((kind, size, {'observation': n}) for size in sizes
                for kind in ('construction', 'memory_traced', 'memory_untraced') for n in range(5))
        construction(list(dict.fromkeys([0, fit] + ([] if full else [8192]))))
        for bucket in (('0', '3-5', '7-9', '15-17', '31-33') if full else ('0', '31-33')):
            for operation in ('key', 'hash', 'lookup', 'identity', 'provider'):
                specifications.append(('history', fit,
                    dict(history_parameters(), bin=bucket, operation=operation)))
        for hands in ((1, 2, 8, 32) if full else (1, 8)):
            for repetition, order in enumerate(('fr', 'rf', 'rf', 'fr')):
                for arm in order:
                    specifications.append(('reuse', fit, dict(hands=hands,
                        repetition=repetition, arm={'f': 'fresh', 'r': 'retained'}[arm],
                        trajectory_ordinals=reuse_ids[:hands])))
        ordinal = diagnostic = 0
        for deal in (range(2) if full else range(1)):
            for seat in (range(6) if full else (0, 3)):
                for lineup in (range(2) if full else range(1)):
                    for size in (0, fit):
                        for strategy in ('blueprint-v1', 'baseline-rules-v1'):
                            selected = (deal == 0 and seat in (0, 2, 3) and lineup == 0
                                        if full else size == fit)
                            modes = ([True, False] if diagnostic % 2 == 0 else [False, True])
                            for mode in modes if selected else [False]:
                                version = 2 if strategy == 'baseline-rules-v1' else 1
                                ident = (f'pontius-v0a-table-session-v{version}-correctness-'
                                         f'r002-{r["id"].replace(".", "")}-{ordinal:03d}-'
                                         + ('d' if mode else 'u'))
                                specifications.append(('session', size, dict(diagnostic=mode,
                                    ordinal=ordinal, deal=deal, seat=seat, lineup=lineup,
                                    strategy=strategy, session_id=ident,
                                    session_path=str(run /
                                        f'sessions/d{deal}-s{seat}-l{lineup}.json'),
                                    blueprint_path=str(run / f'artifacts/{size}.json'))))
                            ordinal += 1
                            diagnostic += selected
        if full:
            construction([n for n in (0, 128, 1024, 8192, 65536) if n not in (0, fit)])
            specifications.extend(('comparison', n, dict(blocks=5, warmups=20,
                calls_per_class=calls, provider_order=['legacy', 'prepared'],
                alternate_provider_first=True, continuous_cycle=True))
                for n, calls in ((1024, 20), (8192, 10), (65536, 2)))
        for kind, size, params in specifications:
            ident = f'r002-{r["id"].replace(".", "")}-{len(cells):05d}'
            argv = [r['executable'], '-B', '-P', str(source / 'tools/v0a_blueprint_workload.py'),
                    'worker', '--source-root', str(source), '--run-root', str(run),
                    '--authorization', r['authorization'], '--cell', ident]
            if kind == 'session' and not params['diagnostic']:
                argv = [r['executable'], '-B', '-P', str(source / 'tools/v0a_table_session.py'),
                    '--session', params['session_path'], '--blueprint', params['blueprint_path'],
                    '--session-id', params['session_id'], '--strategy', params['strategy'],
                    '--auto', '--format', 'json']
            cells.append(dict(id=ident, runtime=r['id'], kind=kind, size=size,
                              parameters=params, argv=argv))
    return cells


def full_run(root, defect=None):
    """Synthetic full-denominator JSON schema fixture, never legal population evidence."""
    objects = {}
    def raw(value):
        return (json.dumps(value, sort_keys=True, separators=(',', ':')) + '\n').encode()
    def put(name, value):
        if name.endswith('/supervision.json'):
            grant = None
            if value['cause'] is None and value['exit_code'] == 0 and (
                    cell['kind'] != 'session' or cell['parameters']['diagnostic']):
                grant = grant_record(name.rsplit('/', 1)[0] + '/worker-grant',
                                     cell, runtime, 'run', run_claim)
            if grant is not None:
                result['captures']['stderr'] = put(name.rsplit('/', 1)[0] + '/stderr.bin',
                                                   grant_wire(grant))
            if defect == 'duplicate_ready':
                stderr_name = name.rsplit('/', 1)[0] + '/stderr.bin'
                result['captures']['stderr'] = put(stderr_name, objects[stderr_name] * 2)
                result.update(status='failed', cause='source_invalid', exit_code=1, observations={})
                value.update(cause='source_invalid', exit_code=1)
            if defect == 'worker_frame':
                failure = dict(version='workload-r002-worker-failure-v1', cell_id=cell['id'],
                    cause='interrupted', secondary=[], exception_type='KeyboardInterrupt')
                stderr_name = name.rsplit('/', 1)[0] + '/stderr.bin'
                result['captures']['stderr'] = put(stderr_name,
                    objects[stderr_name] + b'PONTIUS_WORKLOAD_CONTROL ' + raw(failure))
            value = dict(value, worker_failure=None, worker_grant=grant)
        data = value if type(value) is bytes else raw(value)
        objects[name] = data
        return dict(path=name, bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
    def claim(stage):
        value = dict(version='workload-r002-claim-v2', stage=stage, controller_pid=10,
            controller_created_100ns=1001, source_commit='1' * 40, source_tree='2' * 40,
            source_manifest_sha256=runtimes[0]['source_sha256'], authority_sha256='8' * 64,
            run_root=str(PureWindowsPath(runtimes[0]['run_root'])))
        if defect == 'claim' and stage == 'run':
            value['authority_sha256'] = '7' * 64
        ref = put(stage + '-claim.json', value)
        return value, ref
    def grant_record(prefix, claimed_cell, claimed_runtime, stage, stage_claim):
        if defect == 'grant_missing' and stage == 'run':
            return None
        value, ref = stage_claim
        intent = dict(version='workload-r002-worker-grant-intent-v1', stage=stage,
            cell_id=claimed_cell['id'], runtime_id=claimed_runtime['id'],
            source_commit=value['source_commit'], source_tree=value['source_tree'],
            source_manifest_sha256=claimed_runtime['source_sha256'],
            authority_sha256=value['authority_sha256'], stage_claim_sha256=ref['sha256'],
            runtime_sha256=hashlib.sha256(raw(claimed_runtime)).hexdigest(),
            plan_sha256=plan_ref['sha256'] if stage == 'run' else None,
            cell_sha256=hashlib.sha256(raw(claimed_cell)).hexdigest(), controller_pid=10,
            controller_created_100ns=1001, source_root=claimed_runtime['source_root'],
            run_root=claimed_runtime['run_root'],
            nonce_sha256=hashlib.sha256(prefix.encode()).hexdigest())
        if defect == 'grant' and stage == 'run':
            intent['cell_id'] = 'foreign'
        if defect == 'qualification_grant' and stage == 'qualify':
            intent['plan_sha256'] = 'f' * 64
        intent_ref = put(prefix + '-intent.json', intent)
        receipt = dict(intent, version='workload-r002-worker-grant-v1',
            intent_sha256=intent_ref['sha256'], redirector_pid=7, redirector_created_100ns=1002,
            worker_pid=7, worker_created_100ns=1002, pipe_server_pid=10, pipe_client_pid=10,
            job_member=True, consumed=True)
        put(prefix + '.json', receipt)
        return receipt
    def grant_wire(receipt):
        ready = {key: receipt[key] for key in ('cell_id', 'intent_sha256', 'worker_pid',
                 'worker_created_100ns', 'pipe_server_pid', 'pipe_client_pid')}
        ready['version'] = 'workload-r002-worker-ready-v1'
        return b'PONTIUS_WORKLOAD_GRANT ' + raw(ready)
    runtimes = [dict(control_plan()['runtimes'][0], id=tag, version=version, executable=exe)
        for tag, version, exe in [('3.11', '3.11.15', 'D:/Pontius-tools/py311/Scripts/python.exe'),
                                 ('3.14', '3.14.6', 'D:/Pontius/.venv/Scripts/python.exe')]]
    child_rows = ['d' * 64 + '  src/pontius/__init__.py\n',
                  'c' * 64 + '  tools/v0a_event_adapter.py\n',
                  'b' * 64 + '  tools/v0a_hand_adapter.py\n',
                  'a' * 64 + '  tools/v0a_rehearsal_driver.py\n']
    child_manifest_sha256 = hashlib.sha256(''.join(sorted(child_rows)).encode()).hexdigest()
    source_manifest = ('4' * 64 + '  docs/architecture/v0a-blueprint-workload-r001/'
                       'execution-protocol.md\n' + '8' * 64 +
                       '  docs/architecture/v0a-blueprint-workload-r001/'
                       'invocation-authority.json\n' + ''.join(child_rows)).encode()
    for runtime in runtimes:
        runtime['authorization'] = str(PureWindowsPath(runtime['source_root']) /
            'docs/architecture/v0a-blueprint-workload-r001/invocation-authority.json')
        runtime['source_sha256'] = hashlib.sha256(source_manifest).hexdigest()
        put('admission/' + runtime['id'] + '-source.manifest', source_manifest)
        put('admission/' + runtime['id'] + '-venv.json',
            dict(path=str(PureWindowsPath(runtime['executable']).parents[1] / 'pyvenv.cfg'),
                 sha256='6' * 64))
        put('admission/' + runtime['id'] + '-runtime-stdout.bin', raw(dict(
            version=runtime['version'], resolved=runtime['resolved_executable'],
            implementation='cpython', clocks={
                'monotonic': dict(implementation='GetTickCount64()', monotonic=True,
                                  adjustable=False, resolution=0.015625),
                'perf_counter': dict(implementation='QueryPerformanceCounter()', monotonic=True,
                                     adjustable=False, resolution=1e-7)}))[:-1] + b'\r\n')
        put('admission/' + runtime['id'] + '-runtime-stderr.bin',
            b'failure\n' if defect == 'probe_stderr' else b'')
    if defect == 'authority':
        runtimes[0]['authorization'] = 'D:/alternative.json'
    def environment(runtime):
        return dict(PYTHONPATH=str(PureWindowsPath(runtime['source_root']) / 'src'),
            TEMP=str(PureWindowsPath(runtime['run_root']) / 'temporary' / runtime['id']),
            TMP=str(PureWindowsPath(runtime['run_root']) / 'temporary' / runtime['id']),
            PONTIUS_GIT='C:\\Program Files\\Git\\cmd\\git.exe')
    put('qualification-environment.json', environment(runtimes[0]))
    artifacts = []
    for size in (0, 3, 128, 1024, 8192, 65536):
        entries = [dict(key=dict(version='blueprint-decision-key-v1', token=n),
                        action=dict(kind='check', raise_to=None)) for n in range(size)]
        artifact = dict(version='pontius-blueprint-artifact-v1', source_id='workload-r002-passive',
                        entries=entries)
        file = put(f'artifacts/{size}.json', artifact)
        lengths = [len(raw(entry)) - 1 for entry in entries]
        census = {s: {b: [] for b in ('0', '3-5', '7-9', '15-17', '31-33', 'other')}
                  for s in ('preflop', 'flop', 'turn', 'river')}
        census['preflop']['0'] = lengths
        artifacts.append(dict(size=size, source_sha256='a' * 64, canonical_bytes=30,
            key_bytes=20, wire_bytes=file['bytes'], row_bytes=sum(lengths),
            comma_bytes=max(0, size - 1),
            root_bytes=file['bytes'] - sum(lengths) - max(0, size - 1),
            row_census=census, file=file, labels=[str(size)]))
    queries, chunks = [], []
    for ordinal in range(1152):
        ident = f'r002-query-{ordinal:04d}'
        key = raw(dict(version='blueprint-decision-key-v1', token=ordinal))[:-1]
        context = dict(version='workload-r002-context-v1', id=ident + '-000', trajectory_id=ident,
            factors={}, deal={}, prefix=[], expected=dict(actor=(ordinal % 72) // 12,
                street='preflop',
                history_atoms=0, key_hex=key.hex(), key_sha256=hashlib.sha256(key).hexdigest(),
                decision_sha256='7' * 64, passive_action={}))
        queries.append(dict(version='workload-r002-trajectory-v1', id=ident, factors={}, seed=0,
                            deal={}, contexts=[context], actions=[], settlement={}))
    for index in range(9):
        chunks.append(put(f'population/query-{index:03d}.jsonl',
                          b''.join(raw(t) for t in queries[index * 128:(index + 1) * 128])))
    # Table chunks are retained/hash-bound but not replayed by this pure reader.
    for index in range(32):
        chunks.insert(index, put(f'population/table-{index:03d}.jsonl', b'{}\n'))
    natural = [dict(id=t['contexts'][0]['id'], trajectory_id=t['id'], hit=i < 3,
                    street='preflop', history_atoms=0) for i, t in enumerate(queries)]
    history = {b: dict(hit=[], miss=[]) for b in ('0', '3-5', '7-9', '15-17', '31-33')}
    history['0'] = dict(hit=[t['contexts'][0] for t in queries[:3]],
                        miss=[t['contexts'][0] for t in queries[3:103]])
    selected = dict(version='workload-r002-selections-v1', first_context=queries[0]['contexts'][0],
        natural=natural, history=history,
        reuse=[queries[d * 72 + s * 12 + d % 3 * 2 + d % 2]['contexts']
               for d in range(16) for s in (d % 6, (d + 3) % 6)],
        comparisons={str(n): dict(hit=[t['contexts'][0] for t in queries[:100]],
                     miss=[] if n >= 1152 else [t['contexts'][0] for t in queries[n:n + 100]])
                     for n in (1024, 8192, 65536)})
    if defect == 'natural_missing':
        selected['natural'].pop()
    if defect == 'natural_membership':
        selected['natural'][0]['hit'] = False
    session_config = dict(version='pontius-v0a-table-session-v1', button=0,
        controlled_seat=0, starting_stacks=[200] * 6, small_blind=1, big_blind=2,
        opponents=['passive'] * 6, hands=[dict(private_hands=[[i, i + 1] for i in range(0, 12, 2)],
                                            board_runout=list(range(12, 17)))])
    sessions = [put(f'sessions/d{d}-s{s}-l{l}.json', dict(session_config, controlled_seat=s,
                    opponents=[None if seat == s else 'passive' for seat in range(6)]))
                for d in range(2) for s in range(6) for l in range(2)]
    population = dict(version='workload-r002-population-v1', recipe={'version':
        'workload-r002-recipe-v1'}, table_trajectories=8192, query_trajectories=1152,
        n_fit=3, capacity={}, artifacts=artifacts, chunks=chunks, sessions=sessions,
        selections=put('selections.json', selected), coverage={})
    plan = dict(version='workload-r002-plan-v1',
                population_sha256=put('population.json', population)['sha256'],
                runtimes=runtimes, cells=fixture_schedule(runtimes))
    if defect == 'short_runtime':
        plan['runtimes'] = runtimes[:1]
        plan['cells'] = [c for c in plan['cells'] if c['runtime'] == '3.11']
    if defect == 'short_cell':
        plan['cells'].pop()
    if defect == 'argv':
        plan['cells'][0]['argv'][-1] = 'foreign'
    plan_ref = put('plan.json', plan)
    put('runtimes.json', plan['runtimes'])
    worker_argv = [runtimes[0]['executable'], '-B', '-P',
        str(PureWindowsPath(runtimes[0]['source_root']) / 'tools/v0a_blueprint_workload.py'),
        'worker', '--source-root', str(PureWindowsPath(runtimes[0]['source_root'])),
        '--run-root', str(PureWindowsPath(runtimes[0]['run_root'])),
        '--authorization', runtimes[0]['authorization'], '--cell', 'qualification']
    put('qualification-intent.json', dict(argv=worker_argv,
        recipe_sha256=hashlib.sha256(raw(population['recipe'])).hexdigest()))
    qualification_claim = claim('qualify')
    if defect == 'qualification_missing':
        objects.pop('qualify-claim.json')
    qualification_cell = dict(id='qualification', kind='qualification', runtime='3.11',
        recipe_sha256=hashlib.sha256(raw(population['recipe'])).hexdigest())
    qualification_grant = grant_record('qualification-worker-grant', qualification_cell,
                                       runtimes[0], 'qualify', qualification_claim)
    put('qualification-stdout.bin', b'')
    put('qualification-stderr.bin', grant_wire(qualification_grant))
    put('qualification-result.json', dict(cause='parity_failed' if
        defect == 'qualification_records' else None, secondary=[], exit_code=0,
        truncated=False, samples=[], redirector_pid=7, launch_ns=100,
        outer_ns=10, cleanup_ns=1, cleanup={'verified': True, 'active': 0}, stage_ns=20,
        worker_failure=None, worker_grant=qualification_grant))
    qualification = put('qualification-manifest.json', dict(version='workload-r002-manifest-v1',
        files=[dict(path=n, bytes=len(b), sha256=hashlib.sha256(b).hexdigest())
               for n, b in objects.items()]))
    put('qualified.json', dict(version='workload-r002-qualified-v1', source_commit='1' * 40,
        plan_sha256='0' * 64 if defect == 'qualification' else plan_ref['sha256'],
        manifest=qualification))
    run_claim = claim('run')
    terminal = []
    for cell in plan['cells']:
        runtime = next(r for r in runtimes if r['id'] == cell['runtime'])
        prefix = 'cells/' + cell['id'] + '/'
        put(prefix + 'intent.json', dict(version='workload-r002-intent-v1', cell_id=cell['id'],
            cell=cell, source_sha256=runtime['source_sha256'], protocol_sha256='4' * 64,
            population_sha256=plan['population_sha256']))
        env = environment(runtime)
        if defect == 'environment':
            env['PYTHONPATH'] += '/foreign'
        put(prefix + 'environment.json', env)
        result = control_result(cell['id'])
        if cell == plan['cells'][0]:
            observation = dict(construction_observation(), wire_bytes=artifacts[0]['wire_bytes'])
            result = completed_result(cell['id'], observation)
            capture = {n: put(prefix + n + '.bin', b'') for n in ('stdout', 'stderr')}
            if defect != 'capture':
                result['captures'].update(capture)
            put(prefix + 'observations.json', dict(observation, memory_samples=[],
                prepare_ns=9 if defect == 'observations' else observation['prepare_ns']))
            native = dict(cause=None, secondary=[], exit_code=0, truncated=False,
                samples=observation['memory_samples'], redirector_pid=7, launch_ns=100,
                outer_ns=result['outer_ns'] + int(defect == 'supervision'), cleanup_ns=1,
                cleanup=result['cleanup'])
            put(prefix + 'supervision.json', native)
        if defect == 'context' and cell['kind'] == 'reuse' and cell['parameters']['hands'] == 1:
            obs = dict(memory_samples=memory_samples(), group_ns=100, prepare_ns=[1],
                hash_ns=[] if cell['parameters']['arm'] == 'fresh' else [1], read_ns=1,
                decode_ns=1, query_count=1, distinct_keys=1, context_ids=['foreign'])
            result = completed_result(cell['id'], obs)
            result['captures'].update({n: put(prefix + n + '.bin', b'')
                                       for n in ('stdout', 'stderr')})
            put(prefix + 'observations.json', dict(obs, memory_samples=[]))
            put(prefix + 'supervision.json', dict(cause=None, secondary=[], exit_code=0,
                truncated=False, samples=memory_samples(), redirector_pid=7, launch_ns=100,
                outer_ns=result['outer_ns'], cleanup_ns=1, cleanup=result['cleanup']))
        params = cell['parameters']
        if (defect in ('failed_safety', 'completed_capture') and cell['kind'] == 'session'
                and cell['size'] == 0
                and not params['diagnostic'] and params['deal'] == params['lineup'] == 0
                and params['seat'] == 3 and params['strategy'] == 'blueprint-v1'):
            fixture = failed_fixture(LiteralBinding)
            old = 'r002-311-000-u'
            suffix = params['session_id'].split('-correctness-')[1]
            fixture = json.loads(json.dumps(fixture, default=lambda b: list(b)).replace(
                old, suffix))
            session_raw = objects['sessions/d0-s3-l0.json']
            binding = LiteralBinding.session_binding(session_raw, '1' * 40,
                child_manifest_sha256, artifacts[0]['file']['sha256'], 'a' * 64, 'blueprint-v1')
            fixture['reference']['binding'] = binding
            outer = fixture['outer']
            hand = outer['hands'][0]['result']
            outer['input_sha256'] = binding['session_input_sha256']
            hand['input_sha256'] = binding['hand_input_sha256']
            for row in (outer, hand, fixture['rows'][0]):
                for key in ('source_commit', 'blueprint_artifact_sha256', 'blueprint_sha256'):
                    row[key] = binding[key]
            fixture['rows'][0]['source_manifest_sha256'] = binding['source_manifest_sha256']
            result = dict(control_result(cell['id'], 'failed'), outer_ns=1_000_000_000,
                          exit_code=1, cleanup={'verified': True, 'active': 0})
            result['captures'].update(stdout=put(prefix + 'stdout.bin', packed(fixture)[0]),
                                      stderr=put(prefix + 'stderr.bin', b''))
            if defect == 'completed_capture':
                child_id = fixture['rows'][0]['session_id']
                observation = dict(raw_events=[], session_status='completed', settlement={},
                    reference_id='r002-query-0216', preparation=[dict(hand_id=child_id,
                        preparation_compute_seconds=0.0, post_terminal_compute_seconds=0.0,
                        accounting_complete=True, interrupted_response_count=0)],
                    actions=[dict(id=cell['id'] + '-a1', hand_id=child_id, event_index=0,
                        action_index=1, street='preflop', history_atoms=0, hit=False, first=True,
                        elapsed_ns=1, compute_ns=0, uninstrumented_ns=1, work_cutoff=False,
                        deadline=False, fallback_used=True, selection_origin='blueprint')])
                result.update(status='completed', cause=None, exit_code=0, observations=observation)
            put(prefix + 'supervision.json', dict(cause='worker_failed', secondary=[], exit_code=1,
                truncated=False, samples=[], redirector_pid=7, launch_ns=100,
                outer_ns=result['outer_ns'], cleanup_ns=1, cleanup=result['cleanup']))
            if defect == 'completed_capture':
                put(prefix + 'supervision.json', dict(cause=None, secondary=[], exit_code=0,
                    truncated=False, samples=[], redirector_pid=7, launch_ns=100,
                    outer_ns=result['outer_ns'], cleanup_ns=1, cleanup=result['cleanup']))
        result['files'] = [dict(path=n, bytes=len(b), sha256=hashlib.sha256(b).hexdigest())
                           for n, b in objects.items() if n.startswith(prefix)]
        put(prefix + 'result.json', result)
        terminal.append(dict(cell_id=cell['id'], status=result['status']))
    put('terminal.json', dict(version='workload-r002-terminal-v1', cells=terminal))
    put('run-envelope.json', dict(started_ns=100, finished_ns=1_000_000_100, stop=None))
    failures = [dict(cell_id=None, phase='close', cause='cleanup_failed',
                    exception_type='OSError', detail='literal late close failure')] \
        if defect == 'retention' else []
    put('retention.json', dict(version='workload-r002-retention-v1', complete=True,
                               failures=failures, missing=[]))
    if defect == 'final_refusal':
        put('retention-final-refusal.json', dict(cause='cleanup_failed', interrupted=False,
            original_code='cleanup_failed', exception_type='Refusal', detail='cleanup_failed'))
    put('manifest.json', dict(version='workload-r002-manifest-v1', files=[
        dict(path=n, bytes=len(b), sha256=hashlib.sha256(b).hexdigest())
        for n, b in objects.items()]))
    for name, data in objects.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)


def populate_run(root, defect=None, probe=False):
    population = {'version': 'workload-r002-population-v1',
                  'recipe': {'version': 'workload-r002-recipe-v1'},
                  'table_trajectories': 8192, 'query_trajectories': 1152, 'n_fit': 3,
                  'capacity': {}, 'artifacts': [], 'chunks': [], 'sessions': [],
                  'selections': {'path': 'selections.json', 'bytes': 3,
                                 'sha256': hashlib.sha256(b'{}\n').hexdigest()}, 'coverage': {}}
    plan = control_plan()
    plan['population_sha256'] = hashlib.sha256((json.dumps(population) + '\n').encode()).hexdigest()
    objects = {'plan.json': plan, 'population.json': population, 'selections.json': {},
               'terminal.json': {'version': 'workload-r002-terminal-v1',
                                 'cells': [{'cell_id': 'c' + str(i), 'status': 'unattempted'}
                                           for i in range(3)]}}
    if probe:
        objects['admission/3.11-runtime-stdout.bin'] = {
            'version': '3.11.15', 'resolved': plan['runtimes'][0]['resolved_executable'],
            'implementation': 'cpython', 'clocks': {
                'monotonic': {'implementation': 'GetTickCount64()', 'monotonic': True,
                              'adjustable': False, 'resolution': 0.015625},
                'perf_counter': {'implementation': 'QueryPerformanceCounter()', 'monotonic': True,
                                 'adjustable': False, 'resolution': 1e-7}}}
    for i in range(3):
        prefix = 'cells/c' + str(i) + '/'
        objects[prefix + 'result.json'] = control_result('c' + str(i))
        objects[prefix + 'intent.json'] = {'version': 'workload-r002-intent-v1',
            'cell_id': 'c' + str(i),
            'cell': plan['cells'][i], 'source_sha256': '3' * 64, 'protocol_sha256': '4' * 64,
            'population_sha256': plan['population_sha256']}
        objects[prefix + 'environment.json'] = {'PYTHONPATH': 'D:/source/src'}
    if defect == 'terminal':
        objects['terminal.json']['cells'][0]['status'] = 'completed'
    elif defect == 'population':
        population['n_fit'] += 1
    elif defect == 'intent':
        objects['cells/c0/intent.json']['source_sha256'] = '9' * 64
    elif defect == 'intent_type':
        objects['cells/c1/intent.json'] = json.loads(json.dumps(objects['cells/c1/intent.json']))
        objects['cells/c1/intent.json']['cell']['parameters']['observation'] = True
    elif defect == 'environment':
        objects['cells/c0/environment.json']['PYTHONPATH'] = True
    refs = []
    for name, obj in objects.items():
        raw = (json.dumps(obj) + '\n').encode()
        if name.endswith('-runtime-stdout.bin'):
            raw = raw[:-1] + b'\r\n'
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        refs.append({'path': name, 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()})
    if defect == 'escape':
        refs[0]['path'] = '../plan.json'
    elif defect == 'alias':
        refs[0]['path'] = './plan.json'
    elif defect == 'missing':
        (root / 'plan.json').unlink()
    (root / 'manifest.json').write_bytes((json.dumps(
        {'version': 'workload-r002-manifest-v1', 'files': refs}) + '\n').encode())


def encoded(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
            + "\n").encode()


class LiteralBinding:
    @staticmethod
    def session_binding(raw, commit, manifest, artifact, blueprint, strategy):
        config = json.loads(raw)
        hand = {k: v for k, v in config.items() if k != 'hands'}
        hand.update(config['hands'][0], version='pontius-v0a-table-input-v1')
        return dict(source_commit=commit, source_manifest_sha256=manifest,
            session_input_sha256=hashlib.sha256(raw).hexdigest(),
            hand_input_sha256=hashlib.sha256(encoded(hand)).hexdigest(),
            blueprint_artifact_sha256=artifact, blueprint_sha256=blueprint,
            controlled_seat=config['controlled_seat'], button=config['button'],
            starting_stacks=config['starting_stacks'])


def failed_fixture(extractor, *, version=1, elapsed=15_000_000_001):
    strategy = "baseline-rules-v1" if version == 2 else "blueprint-v1"
    session_id = f"pontius-v0a-table-session-v{version}-correctness-r002-311-000-u"
    child_id = f"pontius-v0a-event-interface-v{version}-correctness-table-r002-311-000-u-h01"
    host_id = f"pontius-v0a-table-host-v{version}-correctness-r002-311-000-u-h01"
    protocol = f"pontius-v0a-event-interface-v{version}"
    config = dict(version="pontius-v0a-table-session-v1", button=0, controlled_seat=3,
        starting_stacks=[200] * 6, small_blind=1, big_blind=2,
        opponents=["passive", "passive", "passive", None, "passive", "passive"],
        hands=[dict(private_hands=[[0,1],[2,3],[4,5],[48,49],[8,9],[10,11]],
                    board_runout=[12,13,14,15,16])])
    session_raw = encoded(config)
    binding = extractor.session_binding(session_raw, "a"*40, "b"*64, "c"*64, "d"*64, strategy)
    cell = dict(id="r002-fixture-session", kind="session", runtime="3.11", size=0,
        parameters=dict(strategy=strategy, session_id=session_id, seat=3))
    selected = dict(kind="call" if version == 2 else "raise", raise_to=None if version == 2 else 4)
    trajectory = dict(contexts=[dict(prefix=[], expected=dict(actor=3, street="preflop",
                                                            history_atoms=0))],
                      actions=[dict(seat=3, street="preflop",
                                    action=dict(kind="raise", raise_to=4))])
    reference = dict(trajectory=trajectory, binding=binding)
    timing = dict(status="completed", interruption_reason=None, wall_start_ns=0,
        last_valid_observation_ns=elapsed, emission_observed_ns=elapsed, elapsed_ns=elapsed,
        response_compute_seconds=elapsed/1_000_000_000, response_uninstrumented_seconds=0.0,
        work_cutoff_crossed=True, deadline_crossed=elapsed>15_000_000_000)
    code = "action_deadline_exceeded" if elapsed>15_000_000_000 else "work_cutoff_exceeded"
    failure = dict(hand_id=child_id, event_index=0, action_index=1, code=code,
        delivery_status="accepted", delivered_action=selected, timing=timing)
    ready = dict(protocol=protocol, session_id=child_id, type="ready", source_commit="a"*40,
        source_manifest_sha256="b"*64, blueprint_artifact_sha256="c"*64,
        blueprint_sha256="d"*64, evidentiary=False)
    decision = None
    if version == 2:
        ready.update(provider=binding["provider"], config_sha256=binding["config_sha256"])
        decision = dict(schema_version="pontius-provider-decision-v1", hand_id=child_id,
            event_index=0,
            action_index=1, street_action_index=1, seat=3, street="preflop",
            state_before_sha256="e"*64, state_after_sha256="f"*64, visible_cards_sha256="1"*64,
            decision_sha256="2"*64, source_manifest_sha256="b"*64, provider=binding["provider"],
            config_sha256=binding["config_sha256"], fallback_blueprint_sha256="d"*64,
            fallback_action=selected, fallback_reason="passive_default",
            proposal=dict(decision_sha256="2"*64, action=dict(kind="raise", raise_to=4),
                          reason="premium_raise"),
            provider_outcome="proposed", selection_reason="provider_late",
            selection_origin="blueprint_fallback",
            selected_action=selected, applied_action=selected, delivery_status="accepted",
            delivered_action=selected, timing=copy.deepcopy(timing), failure_reason=code,
            preparation_use=dict(producer_status="producer_absent", artifact_sha256s=[],
                                 credited_seconds=0))
    rows = [ready,
        dict(protocol=protocol, session_id=child_id, type="action", hand_id=child_id,
             action_index=1,
             seat=3, street="preflop", action=selected),
        dict(protocol=protocol, session_id=child_id, type="event_result", event_index=0,
             status="failed", decision=decision, failure=failure),
        dict(protocol=protocol, session_id=child_id, type="hand_result", complete=False,
             settlement=None,
             rank_source=None, evidentiary=False, preparation_compute_seconds=0.0,
             post_terminal_compute_seconds=0.0, interrupted_response_count=0,
             accounting_complete=True,
             failure_reason=code, secondary_failures=[]),
        dict(protocol=protocol, session_id=child_id, type="session_result", status="failed",
             terminal_publication_compute_seconds=0.0, accounting_complete=True,
             failure_reason=code, secondary_failures=[],
             accounting_scope="runtime_begin_to_final_publication", evidentiary=False)]
    hand = dict(version=f"pontius-v0a-table-session-hand-result-v{version}", session_id=host_id,
        status="failed", failure_reason="child_failed", secondary_failures=[],
        input_sha256=binding["hand_input_sha256"], blueprint_artifact_sha256="c"*64,
        blueprint_sha256="d"*64, source_commit="a"*40,
        applied_actions=[dict(index=0, seat=3, street="preflop", action=selected, origin="bot")],
        settlement=None, child_exit_code=1, child_stdout_base64="", child_stderr_base64="",
        capture_truncated=False)
    outer = dict(version=f"pontius-v0a-table-session-result-v{version}", session_id=session_id,
        status="failed", stop_reason=None, failure_reason="child_failed", secondary_failures=[],
        source_commit="a"*40, input_sha256=binding["session_input_sha256"],
        blueprint_artifact_sha256="c"*64, blueprint_sha256="d"*64, requested_hands=1,
        completed_hands=0, next_button=0, carried_stacks=[200]*6,
        hands=[dict(ordinal=1, button=0, starting_stacks=[200]*6, result=hand)])
    if version == 2:
        for value in (outer, hand):
            value.update(provider=binding["provider"], config_sha256=binding["config_sha256"])
    return dict(cell=cell, reference=reference, rows=rows, outer=outer, session_raw=session_raw)


def packed(fixture, *, rows=None, tail=b""):
    outer = copy.deepcopy(fixture["outer"])
    child = b"".join(encoded(row) for row in (fixture["rows"] if rows is None else rows)) + tail
    outer["hands"][0]["result"]["child_stdout_base64"] = base64.b64encode(child).decode()
    return encoded(outer), child


def completed_schema_fixture(extractor, version):
    """One-response arithmetic/schema fixture; it asserts no legal poker qualification."""
    fixture = failed_fixture(extractor, version=version)
    cell, reference = fixture['cell'], fixture['reference']
    cell['parameters']['diagnostic'] = False
    child_id = fixture['rows'][0]['session_id']
    action = fixture['rows'][1]['action']
    timing = dict(status='completed', interruption_reason=None, wall_start_ns=0,
        last_valid_observation_ns=10, emission_observed_ns=10, elapsed_ns=10,
        response_compute_seconds=0.0, response_uninstrumented_seconds=1e-8,
        work_cutoff_crossed=False, deadline_crossed=False)
    decision = fixture['rows'][2]['decision']
    if version == 1:
        decision = dict(hand_id=child_id, event_index=0, action_index=1,
            street_action_index=1, seat=3, street='preflop', state_before_sha256='e' * 64,
            state_after_sha256='f' * 64, visible_cards_sha256='1' * 64,
            blueprint_sha256=reference['binding']['blueprint_sha256'], selected_action=action,
            selection_reason='passive_default', spine_reason='no_candidate', timing=timing,
            preparation_use=dict(producer_status='producer_absent', artifact_sha256s=[],
                                 credited_seconds=0), failure_reason=None)
    else:
        decision.update(timing=timing, failure_reason=None, selection_reason='provider_selected',
                        selection_origin='provider')
        decision['proposal']['action'] = action
    fixture['rows'][2].update(status='decided', decision=decision, failure=None)
    settlement = dict(reason='schema_fixture', payouts=[0] * 6,
                      final_stacks=[200] * 6, pots=[])
    fixture['rows'][3].update(complete=True, settlement=settlement, rank_source='not_required',
                              failure_reason=None)
    fixture['rows'][4].update(status='completed', failure_reason=None)
    outer = fixture['outer']
    outer.update(status='completed', failure_reason=None, completed_hands=1, next_button=1)
    hand = outer['hands'][0]['result']
    hand.update(status='completed', failure_reason=None, child_exit_code=0, settlement=settlement)
    trajectory = reference['trajectory']
    trajectory.update(id='r002-query-0216', settlement=settlement,
                      actions=[dict(seat=3, street='preflop', action=action)])
    trajectory['contexts'][0]['expected']['key_hex'] = '00'
    observation = dict(raw_events=[], actions=[dict(id=cell['id'] + '-a1', hand_id=child_id,
        event_index=0, action_index=1, street='preflop', history_atoms=0, hit=False, first=True,
        elapsed_ns=10, compute_ns=0, uninstrumented_ns=10, work_cutoff=False, deadline=False,
        fallback_used=version == 1, selection_origin='blueprint' if version == 1 else 'provider')],
        preparation=[dict(hand_id=child_id, preparation_compute_seconds=0.0,
            post_terminal_compute_seconds=0.0, accounting_complete=True,
            interrupted_response_count=0)], session_status='completed', settlement=settlement,
        reference_id=trajectory['id'])
    retained = {'cells/' + cell['id'] + '/stdout.bin': packed(fixture)[0]}
    return completed_result(cell['id'], observation), cell, reference, retained


def counterexamples(fixture):
    """Each yields (name, raw_stdout, expected_bound_fact_count, expected_complete)."""
    clone = copy.deepcopy(fixture)
    clone["rows"][0]["session_id"] = "self-claimed-other-child"
    yield "wrong-ready-child-id", *packed(clone)[:1], 0, False
    clone = copy.deepcopy(fixture)
    clone["outer"]["session_id"] += "-wrong"
    yield "wrong-outer-session-id", *packed(clone)[:1], 0, False
    clone = copy.deepcopy(fixture)
    clone["rows"][2]["failure"]["event_index"] = 1
    yield "wrong-failure-event-id", *packed(clone)[:1], 0, False
    clone = copy.deepcopy(fixture)
    clone["rows"][2]["failure"]["action_index"] = True
    yield "boolean-action-id", *packed(clone)[:1], 0, False
    clone = copy.deepcopy(fixture)
    clone["rows"][2]["failure"]["timing"]["deadline_crossed"] = False
    yield "false-deadline-above-boundary", *packed(clone)[:1], 0, False
    clone = copy.deepcopy(fixture)
    clone["rows"][2]["failure"]["timing"]["response_compute_seconds"] = 1.0
    yield "impossible-timing-partition", *packed(clone)[:1], 0, False
    raw, _ = packed(fixture, rows=fixture["rows"][:3], tail=b'{"invalid":\n')
    yield "valid-failed-prefix-invalid-tail", raw, 1, False
    raw, _ = packed(fixture, rows=fixture["rows"][:3] + [fixture["rows"][2]])
    yield "duplicate-failure-keeps-first-once", raw, 1, False
    clone = copy.deepcopy(fixture)
    clone["outer"]["hands"][0]["result"]["capture_truncated"] = True
    yield "capture-truncated-keeps-bound-fact", *packed(clone)[:1], 1, False
    if fixture["rows"][2]["decision"] is not None:
        clone = copy.deepcopy(fixture)
        clone["rows"][2]["decision"]["delivery_status"] = "unknown"
        yield "v2-mirrored-delivery-mismatch", *packed(clone)[:1], 0, False
        clone = copy.deepcopy(fixture)
        decision = clone["rows"][2]["decision"]
        decision.update(selection_reason="provider_selected", selection_origin="provider")
        decision["proposal"]["action"] = decision["selected_action"]
        yield "v2-provider-selected-with-cutoff", *packed(clone)[:1], 0, False


if __name__ == '__main__':
    unittest.main()
