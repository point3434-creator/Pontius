"""Literal nonempty sessions and real source refusal controls for prepared children."""
import base64
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path.cwd()
FIXTURE = 'tests/fixtures/decision_provider/session.json'
HOST_BLOB = '7beb178989b3ff98b684093ce4022667a1c61ece'


class PreparedTransportTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix='prepared-transport-'))
        artifact = json.loads((ROOT/'tests/fixtures/blueprint_artifact/raise_control.json')
                              .read_bytes())
        # Retain the literal legal key/action fixture; use the first existing explicit deal.
        artifact['entries'][0]['key']['private_hand'] = [50, 51]
        self.blueprint = self.root/'nonempty.json'
        self.blueprint.write_text(json.dumps(artifact), encoding='ascii')

    def session(self, strategy, repo=ROOT, name='session'):
        explicit = [] if strategy is None else ['--strategy', strategy]
        version = 'v2' if strategy == 'baseline-rules-v1' else 'v1'
        argv = [sys.executable, '-B', '-P', str(repo/'tools/v0a_table_session.py'),
            '--session', str(repo/FIXTURE), '--blueprint', str(self.blueprint), '--session-id',
            'pontius-v0a-table-session-'+version+'-correctness-prepared-'+name,
            '--auto', '--format', 'json', *explicit]
        result = subprocess.run(argv, cwd=repo, env=os.environ.copy(),
            capture_output=True, timeout=150)
        (self.root/(name+'-stdout.bin')).write_bytes(result.stdout)
        (self.root/(name+'-stderr.bin')).write_bytes(result.stderr)
        return result

    def clone(self):
        target = self.root/'source'
        argv = [os.environ['PONTIUS_GIT'], '-c', 'core.autocrlf=false',
                '-c', 'core.longpaths=true']
        subprocess.run([*argv, 'clone', '--no-hardlinks', '--no-checkout', str(ROOT),
                        str(target)], check=True, capture_output=True, timeout=120)
        subprocess.run([*argv, '-C', str(target), 'config', 'core.autocrlf', 'false'],
                       check=True, capture_output=True, timeout=30)
        subprocess.run([*argv, '-C', str(target), 'checkout', '--detach', 'HEAD'],
                       check=True, capture_output=True, timeout=120)
        return target

    def test_three_hand_nonempty_hit_miss_sessions_keep_literal_actions_and_settlements(self):
        reports = []
        finals = [[200, 199, 198, 203, 200, 200], [200, 199, 197, 204, 200, 200],
                  [200, 199, 197, 206, 198, 200]]
        for strategy in (None, 'blueprint-v1', 'baseline-rules-v1'):
            name = strategy or 'default'
            with self.subTest(strategy=name):
                process = self.session(strategy, name=name)
                self.assertEqual(process.returncode, 0, (process.stdout, process.stderr))
                report = json.loads(process.stdout)
                self.assertEqual(report['status'], 'completed')
                self.assertEqual(report['completed_hands'], 3)
                self.assertEqual(report['carried_stacks'], finals[-1])
                self.assertIsNone(report['failure_reason'])
                self.assertEqual(report['secondary_failures'], [])
                self.assertEqual([entry['button'] for entry in report['hands']], [0, 1, 2])
                baseline = strategy == 'baseline-rules-v1'
                expected_first = [(3, 'preflop', 'raise', 4 if baseline else 6)]
                expected_first += [(seat, 'preflop', 'fold', None) for seat in (4, 5, 0, 1, 2)]
                expected_second = [(seat, 'preflop', 'fold', None) for seat in (4, 5, 0, 1, 2)]
                expected_third = [(seat, 'preflop', 'fold', None) for seat in (5, 0, 1, 2)]
                if baseline:
                    expected_third += [(3, 'preflop', 'raise', 4), (4, 'preflop', 'fold', None)]
                else:
                    expected_third += [(3, 'preflop', 'call', None), (4, 'preflop', 'check', None)]
                    expected_third += [(seat, street, 'check', None)
                        for street in ('flop', 'turn', 'river') for seat in (3, 4)]
                expected = (expected_first, expected_second, expected_third)
                fallback_reasons = []
                for index, (entry, final, actions) in enumerate(zip(report['hands'], finals,
                                                                              expected)):
                    hand = entry['result']
                    self.assertEqual(entry['starting_stacks'], [200]*6 if index == 0
                                     else finals[index-1])
                    self.assertEqual(hand['status'], 'completed')
                    self.assertEqual(hand['settlement']['final_stacks'], final)
                    self.assertEqual(hand['child_exit_code'], 0)
                    self.assertFalse(hand['capture_truncated'])
                    self.assertIsNone(hand['failure_reason'])
                    self.assertEqual(hand['secondary_failures'], [])
                    self.assertEqual(hand['child_stderr_base64'], '')
                    observed = [(row['seat'], row['street'], row['action']['kind'],
                                 row['action']['raise_to']) for row in hand['applied_actions']]
                    self.assertEqual(observed, actions)
                    frames = [json.loads(row) for row in
                              base64.b64decode(hand['child_stdout_base64']).splitlines()]
                    self.assertEqual(frames[0]['type'], 'ready')
                    for frame in frames:
                        if frame['type'] == 'event_result' and frame['decision']:
                            decision = frame['decision']
                            reason = 'fallback_reason' if baseline else 'selection_reason'
                            fallback_reasons.append(decision[reason])
                            if baseline:
                                self.assertEqual(decision['fallback_action'],
                                    {'kind': 'raise', 'raise_to': 6} if index == 0 else
                                    {'kind': 'call', 'raise_to': None})
                self.assertEqual(fallback_reasons, ['table_hit', 'passive_default'] if baseline
                                 else ['table_hit']+['passive_default']*4)
                reports.append(report)
        for left, right in zip(reports[0]['hands'], reports[1]['hands']):
            self.assertEqual(left['result']['applied_actions'], right['result']['applied_actions'])
            self.assertEqual(left['result']['settlement'], right['result']['settlement'])

    def test_changed_unexcepted_source_extra_preparation_and_wrong_session_pin_refuse(self):
        repo = self.clone()
        changes = ('src/pontius/v0a/model.py', 'src/pontius/blueprint_preparation/extra.py',
                   'tools/v0a_table_session.py')
        for index, relative in enumerate(changes):
            with self.subTest(path=relative):
                path = repo/relative
                original = path.read_bytes() if path.exists() else None
                raw = original or b''
                if relative.endswith('v0a_table_session.py'):
                    self.assertEqual(raw.count(HOST_BLOB.encode()), 1)
                    changed = raw.replace(HOST_BLOB.encode(), b'0'*40)
                else:
                    changed = raw+b'\n# controlled source drift\n'
                path.write_bytes(changed)
                try:
                    result = self.session('baseline-rules-v1', repo, 'refusal-'+str(index))
                    self.assertNotEqual(result.returncode, 0)
                    report = json.loads(result.stdout)
                    self.assertEqual(report['status'], 'failed')
                    self.assertEqual(report['failure_reason'], 'source_invalid')
                    self.assertEqual(report['hands'], [])
                finally:
                    if original is None:
                        path.unlink()
                    else:
                        path.write_bytes(original)

    def test_loaded_host_rechecks_prepared_bytes_and_loaded_origin_after_admission(self):
        repo = self.clone()
        prefix = """import runpy, sys
from pathlib import Path
module = runpy.run_path('tools/v0a_table_host.py')
source = module['Source'](Path.cwd())
source.load()
print('ADMITTED', flush=True)
"""
        controls = ("""path = Path('src/pontius/blueprint_preparation/lookup.py')
raw = path.read_bytes()
try:
    path.write_bytes(raw+b'\\n# late drift\\n')
    source.check()
finally:
    path.write_bytes(raw)
""", """sys.modules['pontius.blueprint_preparation.lookup'].__file__ = str(
    Path.cwd()/'foreign.py')
source.check()
""")
        for index, control in enumerate(controls):
            with self.subTest(control=index):
                result = subprocess.run([sys.executable, '-B', '-P', '-c', prefix+control],
                    cwd=repo, env=dict(os.environ, PYTHONPATH=str(repo/'src')),
                    capture_output=True, timeout=90)
                (self.root/('late-'+str(index)+'-stdout.bin')).write_bytes(result.stdout)
                (self.root/('late-'+str(index)+'-stderr.bin')).write_bytes(result.stderr)
                self.assertIn(b'ADMITTED', result.stdout, result.stderr)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(b'source_invalid', result.stderr)


if __name__ == '__main__':
    unittest.main()
