"""Literal arithmetic and adverse retained-record controls; no measured workloads."""
import hashlib
import importlib.util
import json
from pathlib import Path
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
        result = report.summarize(records, plan)['runtimes']['3.11']
        self.assertEqual(result['traffic']['natural']['raw'], [100])
        self.assertEqual(result['profile_cases'][0]['phases']['orchestration'], 1000)
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

    def test_census_rejects_duplicates_unknown_cells_and_wrong_types(self):
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
            populate_run(root)
            before = {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob('*')
                      if p.is_file()}
            loaded = report.read_run(root)
            self.assertEqual(loaded['summary']['census']['unattempted'], ['c0', 'c1', 'c2'])
            self.assertFalse(loaded['runtime_clocks']['3.11']['available'])
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
            populate_run(root, probe=True)
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
        for defect in ('escape', 'alias', 'missing', 'terminal', 'population', 'intent',
                       'intent_type', 'environment'):
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                populate_run(root, defect)
                with self.subTest(defect=defect), self.assertRaises(ValueError):
                    report.read_run(root)

    def test_json_duplicate_keys_and_nonfinite_refuse(self):
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


if __name__ == '__main__':
    unittest.main()
