"""Finite zero-seed legal controls; never execute the future population recipe."""
from __future__ import annotations
import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / 'tools/v0a_blueprint_workload_population.py'
FIXTURE = json.loads((ROOT / 'tests/fixtures/blueprint_workload/control.json').read_bytes())


class BlueprintWorkloadPopulationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = None
        if TOOL.is_file():
            spec = importlib.util.spec_from_file_location('population_control', TOOL)
            cls.module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(cls.module)
            cls.traces = [cls.module.trajectory(cls.module.factors('table', i),
                          seed=FIXTURE['seed']) for i in (0, 6, 12, 18)]
            cls.queries = [cls.module.trajectory(cls.module.factors('query', i),
                           seed=FIXTURE['seed']) for i in range(6)]

    def setUp(self):
        self.assertIsNotNone(self.module, 'population contract implementation is absent')
        self.m = self.module

    def test_recipe_ordinals_and_disjoint_domains(self):
        # A reversed factor radix would select a different real policy/seat.
        self.assertEqual([self.m.factors('table', i)[k] for i, k in
                          ((5, 'button'), (6, 'stack_profile'), (12, 'lineup'))], [5, 1, 1])
        self.assertEqual([self.m.factors('query', 1151)[k] for k in
                          ('deal_ordinal', 'controlled_seat', 'stack_profile', 'lineup',
                           'strategy')], [15, 5, 1, 2, 'baseline-rules-v1'])
        self.assertNotEqual(self.m.seed_for('table', 0), self.m.seed_for('query', 0))
        for corpus, ordinal in [('query', True), ('table', 8192), ('query', 1152)]:
            with self.assertRaises(self.m.Refusal):
                self.m.factors(corpus, ordinal)

    def test_literal_deal_actions_and_settlement(self):
        # Wrong turn order, raise-once semantics or terminal handling fails literal outcomes.
        for index, prefix in ((0, 'passive'), (2, 'minimum_raise')):
            trace = self.traces[index]
            self.assertEqual(trace['deal'], FIXTURE['deal'])
            self.assertEqual(len(trace['actions']), FIXTURE[prefix + '_actions'])
            self.assertEqual(trace['settlement']['final_stacks'],
                             FIXTURE[prefix + '_final_stacks'])
        self.assertEqual([r['seat'] for r in self.traces[0]['actions'][:6]],
                         FIXTURE['passive_first_seats'])
        self.assertEqual([r['action']['kind'] for r in self.traces[0]['actions'][:6]],
                         FIXTURE['passive_first_actions'])
        self.assertEqual([r['action']['raise_to'] for r in self.traces[2]['actions'][:6]],
                         FIXTURE['minimum_raise_first_amounts'])

    def test_replay_visible_context_and_fresh_equal_keys(self):
        # Hidden-card exposure or returning stored key objects breaks the ownership boundary.
        record = self.traces[0]['contexts'][7]
        first, second = self.m.replay_context(record), self.m.replay_context(record)
        self.assertEqual(first.cards.private_hand, tuple(FIXTURE['deal']['private_hands'][2]))
        self.assertEqual(first.cards.board, tuple(FIXTURE['deal']['board_runout'][:3]))
        self.assertFalse(hasattr(first.cards, 'private_hands'))
        key1, key2 = self.m.context_key(first), self.m.context_key(second)
        self.assertEqual(key1, key2)
        self.assertIsNot(key1, key2)
        self.assertEqual(key1.canonical_bytes().hex(), record['expected']['key_hex'])

    def test_context_refuses_illegal_or_corrupt_witness(self):
        # An arbitrary history edit or bool integer must never reconstruct an observation.
        record = self.traces[0]['contexts'][3]
        for mutation in ('extra', 'bool', 'seat', 'key', 'raise', 'oversize', 'action_bool'):
            bad = copy.deepcopy(record)
            if mutation == 'extra': bad['unknown'] = 1
            if mutation == 'bool': bad['factors']['button'] = False
            if mutation == 'seat': bad['prefix'][0]['seat'] = 0
            if mutation == 'key': bad['expected']['key_hex'] = '00'
            if mutation == 'raise': bad['prefix'][0]['action'] = {'kind': 'raise', 'raise_to': 1}
            if mutation == 'oversize': bad['prefix'] *= 100
            if mutation == 'action_bool': bad['expected']['passive_action']['raise_to'] = False
            with self.assertRaises(self.m.Refusal): self.m.replay_context(bad)

    def test_deduplication_first_witness_and_street_interleaving(self):
        # Sorting by codec order or overwriting duplicates changes prescribed membership.
        contexts = self.traces[0]['contexts']
        members = self.m.interleave([contexts + contexts])
        self.assertEqual([r['id'] for r in members[:8]],
                         [contexts[i]['id'] for i in (0, 6, 12, 18, 1, 7, 13, 19)])
        self.assertEqual(len(members), 24)
        self.assertTrue(hasattr(self.m, 'TableMembers'), 'bounded admitted-entry collector absent')
        collector = self.m.TableMembers(2)
        for record in contexts + contexts:
            collector.add(record, self.m.replay_context(record))
        rows = collector.ordered()
        self.assertEqual([self.m.member_context(row)['id'] for row in rows],
                         [contexts[i]['id'] for i in (0, 6, 12, 18, 1, 7, 13, 19)])
        self.assertEqual(self.m._artifact_rows(rows)[0], self.m.artifact(members[:8])[0])
        selected = self.m._select_rows(rows, self.queries)
        self.assertEqual(selected['history']['0']['hit'][0], contexts[0])

    def test_exact_codec_bytes_and_member_prefix_capacity(self):
        # Losing commas, root bytes or selecting sorted-prefix keys changes capacity.
        members = self.m.interleave([t['contexts'] for t in self.traces])
        sizes = (0, 1, 16, 128)
        self.assertGreaterEqual(len(members), 128)
        for size in sizes:
            raw, metadata = self.m.artifact(members[:size])
            self.assertEqual(metadata['wire_bytes'], len(raw))
            self.assertEqual(metadata['root_bytes'] + metadata['row_bytes'] +
                             metadata['comma_bytes'], len(raw))
        cap = self.m.artifact(members[:16])[1]['wire_bytes']
        self.assertEqual(self.m.capacity(members, cap)['n_fit'], 16)
        self.assertEqual(self.m.prefix_capacity([10, 20, 30], 5, 36), 2)
        with self.assertRaises(self.m.Refusal): self.m.capacity(members, 10**9)
        entry = self.m._entry(members[0])
        with self.assertRaises(self.m.Refusal) as oversized:
            self.m._artifact_rows([(entry, members[0], self.m.FILE_LIMIT)])
        self.assertEqual(oversized.exception.code, 'capture_limit')

    def test_missing_coverage_and_action_cap_refuse(self):
        # Truncation must not produce a qualified hand or invent missing history bins.
        with self.assertRaises(self.m.Refusal) as failed:
            self.m.trajectory(self.m.factors('table', 0), seed=FIXTURE['seed'], max_actions=1)
        self.assertEqual(failed.exception.code, 'coverage_missing')
        with self.assertRaises(self.m.Refusal): self.m.qualify_coverage(self.traces, self.queries)

    def test_query_sequences_and_reuse_selection(self):
        # Opponent observations entering query traffic inflate denominators.
        for trace in self.queries:
            self.assertTrue(all(r['expected']['actor'] == 0 for r in trace['contexts']))
            self.assertEqual([len(r['prefix']) for r in trace['contexts']],
                             sorted(len(r['prefix']) for r in trace['contexts']))
        expected = [0, 36, 87, 123, 172, 208]
        self.assertEqual(self.m.reuse_ordinals()[:6], expected)
        self.assertEqual(len(set(self.m.reuse_ordinals())), 32)
        self.assertEqual(self.queries[1]['actions'][3]['action']['kind'], 'fold')
        self.assertEqual([r['expected']['history_atoms'] for r in self.queries[4]['contexts']],
                         [3, 9, 16, 26, 36])

    def test_selection_natural_membership_and_history_bins(self):
        # Natural hit labels must use the actual prefix and keep uncovered classes empty.
        members = self.m.interleave([self.traces[0]['contexts']])
        selection = self.m.select_contexts(members[:1], self.queries)
        self.assertEqual(len(selection['history']['0']['hit']), 1)
        self.assertEqual(selection['history']['31-33']['hit'], [])
        self.assertTrue(all(type(r['hit']) is bool for r in selection['natural']))
        self.assertTrue(all(not r['hit'] for r in selection['natural']))
        self.assertEqual([self.m.history_bin(n) for n in (0, 2, 3, 6, 8, 16, 32, 34)],
                         ['0', 'other', '3-5', 'other', '7-9', '15-17', '31-33', 'other'])

    def test_fixed_plan_counts_unique_sizes_and_session_order(self):
        # Duplicate coincident sizes or doubled 3.14 cases changes frozen denominators.
        manifest = {'version': 'workload-r002-population-v1', 'n_fit': 8192,
                    'artifacts': [{'size': n, 'file': {'path': f'artifacts/{n}.json'}}
                                  for n in (0, 128, 1024, 8192, 65536)]}
        runtimes = [dict(id=i, version=v, executable=e, executable_sha256='a'*64,
                        resolved_executable=f'C:/runtime-{i}/python.exe',
                        resolved_executable_sha256='d'*64,
                        authorization='D:/authorization.json',
                        source_root='D:/snapshot', run_root='D:/run', source_sha256='b'*64,
                        protocol_sha256='c'*64) for i, v, e in
                    [('3.11', '3.11.15', 'D:/Pontius-tools/py311/Scripts/python.exe'),
                     ('3.14', '3.14.6', 'D:/Pontius/.venv/Scripts/python.exe')]]
        plan = self.m.freeze_plan(manifest, runtimes)
        self.assertEqual(plan['runtimes'], runtimes)
        cells = plan['cells']
        for cell in cells:
            runtime = next(r for r in runtimes if r['id'] == cell['runtime'])
            self.assertEqual(cell['argv'][0], runtime['executable'])
        self.assertEqual(len({c['id'] for c in cells}), len(cells))
        sessions = [c for c in cells if c['kind'] == 'session']
        self.assertEqual(sum(not c['parameters']['diagnostic'] for c in sessions), 104)
        self.assertEqual(sum(c['parameters']['diagnostic'] for c in sessions), 16)
        self.assertEqual(len([c for c in cells if c['kind'] == 'construction']), 35)
        self.assertEqual(len([c for c in cells if c['kind'] == 'reuse']), 48)
        self.assertEqual(len([c for c in cells if c['kind'] == 'history']), 35)
        self.assertEqual(len([c for c in cells if c['kind'] == 'comparison']), 3)
        self.assertTrue(sessions[0]['parameters']['diagnostic'])
        self.assertFalse(sessions[1]['parameters']['diagnostic'])
        for cell in sessions:
            params = cell['parameters']
            prefix = ('pontius-v0a-table-session-v2-correctness-' if
                      params['strategy'] == 'baseline-rules-v1' else
                      'pontius-v0a-table-session-v1-correctness-')
            self.assertTrue(params['session_id'].startswith(prefix), params['session_id'])
            self.assertLessEqual(len(params['session_id']) - len(prefix), 40)
        self.assertEqual(cells[-1]['runtime'], '3.14')
        self.assertNotIn(65536, [c['size'] for c in cells if c['runtime'] == '3.14'])
        for mutation in ('version', 'extra', 'hash', 'relative'):
            invalid = copy.deepcopy(runtimes)
            if mutation == 'version': invalid[0]['version'] = '3.11.16'
            if mutation == 'extra': invalid[0]['plugin'] = 'anything'
            if mutation == 'hash': invalid[0]['executable_sha256'] = 'NaN'
            if mutation == 'relative': invalid[0]['source_root'] = 'source'
            with self.assertRaises(self.m.Refusal): self.m.freeze_plan(manifest, invalid)
        for index, runtime in enumerate(runtimes):
            changes = [(field, False) for field in runtime]
            changes += [(field, 'NaN') for field in runtime if field.endswith('_sha256')]
            for field in ('executable', 'resolved_executable', 'source_root', 'run_root',
                          'authorization'):
                changes.extend((field, path) for path in ('relative', 'D:/x/../python.exe'))
                if field != 'resolved_executable':
                    changes.append((field, 'C:/displaced'))
            for field, value in changes:
                with self.subTest(runtime=runtime['id'], field=field, value=value):
                    invalid = copy.deepcopy(runtimes)
                    invalid[index][field] = value
                    with self.assertRaises(self.m.Refusal):
                        self.m.freeze_plan(manifest, invalid)


if __name__ == '__main__':
    unittest.main()
