from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[1]
TOOL = 'tools/v0a_hand_adapter.py'
PREFIX = 'pontius-v0a-hand-replay-v1-correctness-adapter-'
FIXTURES = REPO / 'tests/fixtures/hand_adapter'


def document(name='raise'):
    return json.loads((FIXTURES / f'{name}_scenario.json').read_bytes())


def wire(value):
    return json.dumps(value, ensure_ascii=True).encode('ascii')


class AdapterTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue((REPO / TOOL).is_file(), 'The approved real CLI is not implemented')
        parent = REPO.parent if REPO.drive.upper() == 'D:' else Path('D:/')
        self.directory = Path(tempfile.mkdtemp(prefix='hand-adapter-', dir=parent))
        self.repo = self.directory / 'source'
        subprocess.run([os.environ['PONTIUS_GIT'], '-c', 'core.autocrlf=false',
                        '-c', 'advice.detachedHead=false', 'clone',
                        '--quiet', '--no-hardlinks', str(REPO), str(self.repo)], check=True)
        self.sequence = 0

    def git(self, *args, data=None):
        return subprocess.run([os.environ['PONTIUS_GIT'], '--no-replace-objects', '-C',
                               str(self.repo), *args], input=data, check=True,
                              capture_output=True).stdout.strip()

    def invoke(self, name='raise', scenario=None, policy=None, extra=(), code=None, env=None):
        self.sequence += 1
        run_id = PREFIX + f'{self.directory.name}-{self.sequence}'
        root = self.directory / run_id
        root.mkdir()
        scenario_path, policy_path = (self.directory / f'{self.sequence}-{kind}.json'
                                      for kind in ('scenario', 'blueprint'))
        scenario_path.write_bytes(scenario or (FIXTURES / f'{name}_scenario.json').read_bytes())
        policy_path.write_bytes(policy or (FIXTURES / f'{name}_blueprint.json').read_bytes())
        args = ['--scenario', str(scenario_path), '--blueprint', str(policy_path),
                '--run-id', run_id, '--run-root', str(root), *extra]
        child = {k: v for k, v in os.environ.items()
                 if not k.upper().startswith(('GIT_', 'PYTHON', 'PONTIUS_'))}
        child.update(PYTHONPATH=str(self.repo / 'src'), PONTIUS_GIT=os.environ['PONTIUS_GIT'])
        child.update(env or {})
        command = ['-c', code] if code is not None else [str(self.repo / TOOL)]
        result = subprocess.run([sys.executable, '-B', '-P', *command, *args],
                                cwd=self.repo, env=child, capture_output=True, timeout=90)
        return result, root, scenario_path, policy_path

    def accepted(self, result, root):
        self.assertEqual(result.returncode, 0, result.stderr.decode(errors='replace'))
        self.assertEqual(result.stderr, b'')
        self.assertEqual((result.stdout.count(b'\n'), b'\r' in result.stdout), (1, False))
        summary = json.loads(result.stdout)
        self.assertIs(summary['passed'], True)
        self.assertIs(summary['evidentiary'], False)
        self.assertEqual(summary['mode'], 'correctness')
        self.assertEqual(summary['run_id'], root.name)
        self.assertEqual(summary['source_commit'], self.git('rev-parse', 'HEAD').decode())
        digest = hashlib.sha256((root / 'trace.jsonl').read_bytes()).hexdigest()
        self.assertEqual(summary['trace_sha256'], digest)
        return summary

    def refused(self, result, root, *, pre_run=False):
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertEqual(result.stdout, b'')
        self.assertIn(b'REFUSED', result.stderr)
        if pre_run:
            self.assertEqual(list(root.iterdir()), [])

    def test_real_cli_raise_showdown_miss_and_changed_raw_inputs(self):
        for name, stacks, hits, fallbacks in (
                ('raise', [200, 199, 198, 203, 200, 200], 1, 0),
                ('showdown', [210, 198, 198, 198, 198, 198], 1, 3)):
            result, root, scenario, policy = self.invoke(name)
            summary = self.accepted(result, root)
            self.assertEqual(summary['final_stacks'], stacks)
            self.assertEqual(summary['payouts'], document(name)['expected']['payouts'])
            self.assertEqual(summary['actions'], document(name)['expected']['controlled_actions'])
            self.assertEqual((summary['table_hits'], summary['passive_fallbacks']),
                             (hits, fallbacks))
            for key, path in (('scenario_sha256', scenario), ('blueprint_artifact_sha256', policy)):
                self.assertEqual(summary[key], hashlib.sha256(path.read_bytes()).hexdigest())
            first = summary
        data = document()
        data['expected']['controlled_actions'][0].update(kind='call', raise_to=None,
                                                        selection_reason='passive_default')
        policy = json.loads((FIXTURES / 'raise_blueprint.json').read_bytes())
        policy['entries'][0]['key']['private_hand'] = [1, 13]
        result, root, _, _ = self.invoke(scenario=wire(data), policy=wire(policy))
        self.refused(result, root)  # A free big-blind check cannot be replaced by a fold.
        data = document('showdown')
        data['expected']['controlled_actions'][0]['selection_reason'] = 'passive_default'
        policy = json.loads((FIXTURES / 'showdown_blueprint.json').read_bytes())
        policy['entries'][0]['key']['private_hand'] = [0, 12]
        result, root, _, _ = self.invoke(scenario=wire(data), policy=wire(policy))
        summary = self.accepted(result, root)
        self.assertEqual((summary['table_hits'], summary['passive_fallbacks']), (0, 4))
        self.assertEqual(summary['final_stacks'], [210, 198, 198, 198, 198, 198])
        for key in ('scenario_sha256', 'blueprint_artifact_sha256',
                    'blueprint_sha256', 'semantic_sha256'):
            self.assertNotEqual(first[key], summary[key])

    def test_real_semantic_and_expectation_refusals(self):
        for path, value in (
                (('opponent_actions', 0, 'seat'), 5),
                (('opponent_actions', 6, 'street'), 'preflop'),
                (('opponent_actions', 0), dict(street='preflop', seat=4, kind='raise', raise_to=1)),
                (('opponent_actions',), []),
                (('opponent_actions',), document('showdown')['opponent_actions'] * 2),
                (('expected', 'controlled_actions'), []), (('expected', 'pots'), [6]),
                (('expected', 'payouts'), [0, 0, 0, 4, 0, 0]),
                (('expected', 'controlled_actions', 0, 'kind'), 'fold'),
                (('expected', 'controlled_actions', 0, 'selection_reason'), 'passive_default'),
                (('hands',), document()['hands'][:5])):
            data = document('showdown')
            target = data
            for part in path[:-1]:
                target = target[part]
            target[path[-1]] = value
            result, root, _, _ = self.invoke(name='showdown', scenario=wire(data))
            self.refused(result, root)
        policy = json.loads((FIXTURES / 'raise_blueprint.json').read_bytes())
        policy['entries'][0]['action']['raise_to'] = 1000
        result, root, _, _ = self.invoke(policy=wire(policy),
            code=self.instrument('assert not host.mailbox.accepted'))
        self.refused(result, root)
        self.assertIn(b'HOST:', result.stderr)
        trace = root / 'trace.jsonl'
        self.assertNotIn(b'"record_type":"decision"', trace.read_bytes() if trace.exists() else b'')

    def test_input_identity_and_source_refusals_preserve_bytes(self):
        for extra, env, code in (
                (('--run-id', 'wrong'), {}, None), (('--run-root', str(self.directory)), {}, None),
                (('--scenario', str(self.directory / 'absent')), {}, None),
                ((), {'PONTIUS_GIT': ''}, None),
                ((), {}, "from pathlib import Path; import runpy; p=Path('tools/copied.py'); "
                 "p.write_bytes(Path('tools/v0a_hand_adapter.py').read_bytes()+b'\\n# copy\\n'); "
                 "runpy.run_path(str(p),run_name='__main__')"),
                ((), {}, "import pontius,runpy;"
                 "runpy.run_path('tools/v0a_hand_adapter.py',run_name='__main__')")):
            result, root, _, _ = self.invoke(extra=extra, env=env, code=code)
            self.refused(result, root, pre_run=True)
        for relative in ('src/pontius/hand_scenario/codec.py', 'src/pontius/river.py',
                         'src/pontius/hand_scenario/extra.py', 'tools/v0a_hand_adapter.py'):
            path = self.repo / relative
            original = path.read_bytes() if path.exists() else None
            path.write_bytes((original or b'') + b'\n# owned drift\n')
            result, root, _, _ = self.invoke()
            self.refused(result, root, pre_run=True)
            self.assertEqual(path.read_bytes(), (original or b'') + b'\n# owned drift\n')
            path.unlink() if original is None else path.write_bytes(original)

    def test_raw_commit_and_blob_replacement_objects(self):
        path = self.repo / 'src/pontius/hand_scenario/codec.py'
        original = path.read_bytes()
        changed = original + b'\n# real replacement control\n'
        old = self.git('rev-parse', 'HEAD').decode()
        blob = self.git('rev-parse', 'HEAD:src/pontius/hand_scenario/codec.py').decode()
        replacement = self.git('hash-object', '-w', '--stdin', data=changed).decode()
        self.git('replace', blob, replacement)
        self.accepted(*self.invoke()[:2])  # A ref alone does not change executed raw bytes.
        path.write_bytes(changed)
        self.refused(*self.invoke()[:2], pre_run=True)
        self.git('add', 'src/pontius/hand_scenario/codec.py')
        tree = self.git('write-tree').decode()
        commit = self.git('-c', 'user.name=Test', '-c', 'user.email=test@localhost',
                          'commit-tree', tree, '-p', old, '-m', 'owned replacement').decode()
        self.git('replace', old, commit)
        self.refused(*self.invoke(env={'GIT_NO_REPLACE_OBJECTS': '0'})[:2], pre_run=True)
        self.assertEqual(self.git('rev-parse', 'HEAD').decode(), old)

    def instrument(self, after):
        return """import json, runpy, sys, hashlib
from pathlib import Path
from dataclasses import replace
g = runpy.run_path('tools/v0a_hand_adapter.py')['main'].__globals__
original_load = g['Source'].load
def load(source):
    modules = original_load(source)
    original_run = modules[2].ReplayHost.run
    def run(host, **kwargs):
        out = original_run(host, **kwargs)
        path = Path(kwargs['run_root']) / 'trace.jsonl'
        raw = path.read_bytes() if path.exists() else b''
        passed = out.receipt.passed
""" + '\n'.join('        ' + line for line in after.splitlines()) + """
        retained = path.read_bytes() if path.exists() else b''
        audit = dict(host_passed=passed, accepted=len(host.mailbox.accepted),
                     retained_sha256=hashlib.sha256(retained).hexdigest())
        (path.parent.parent / (path.parent.name + '-audit.json')).write_text(json.dumps(audit))
        return out
    modules[2].ReplayHost.run = run
    return modules
g['Source'].load = load
raise SystemExit(g['main']())
"""

    def test_real_host_persisted_readback_faults_and_bad_success_falsifier(self):
        for change in (
                "out = replace(out, receipt=replace(out.receipt, passed=False))",
                "out = replace(out, receipt=replace(out.receipt, accounting_complete=False))",
                "out = replace(out, receipt=replace(out.receipt, run_id='wrong'))",
                "out = replace(out, receipt=replace(out.receipt, trace_sha256='0'*64))",
                "path.write_bytes(raw + b'!')",
                "path.write_bytes(raw + b'!')\nout = replace(out, trace=raw+b'!', "
                "receipt=replace(out.receipt, trace_sha256=hashlib.sha256(raw+b'!').hexdigest()))",
                "(source.repo / 'src/pontius/hand_scenario/drift.py')"
                ".write_bytes(b'# late drift\\n')"):
            result, root, _, _ = self.invoke(code=self.instrument(change))
            self.refused(result, root)
            audit = json.loads((self.directory / (root.name + '-audit.json')).read_bytes())
            self.assertTrue(audit['host_passed'])
            self.assertEqual(audit['accepted'], 1)
            digest = hashlib.sha256((root / 'trace.jsonl').read_bytes()).hexdigest()
            self.assertEqual(audit['retained_sha256'], digest)
        (self.repo / 'src/pontius/hand_scenario/drift.py').unlink()
        data = document()
        data['expected']['controlled_actions'][0]['raise_to'] = 7
        self.refused(*self.invoke(scenario=wire(data))[:2])
        result, root, _, _ = self.invoke(scenario=wire(data),
            code=self.instrument("g['require'] = lambda *args: None"))
        summary = self.accepted(result, root)  # The bad behavior must actually occur.
        self.assertEqual(summary['actions'][0]['raise_to'], 6)
        self.assertRaises(AssertionError, self.refused, result, root)

    def test_reparse_input_and_existing_trace_are_not_overwritten(self):
        result, root, scenario, _ = self.invoke()
        self.accepted(result, root)
        raw = (root / 'trace.jsonl').read_bytes()
        self.refused(*self.invoke(extra=('--run-root', str(root), '--run-id', root.name))[:2])
        self.assertEqual((root / 'trace.jsonl').read_bytes(), raw)
        link = self.directory / 'junction'
        subprocess.run([os.environ['COMSPEC'], '/c', 'mklink', '/J', str(link), str(self.repo)],
                       check=True, capture_output=True)
        linked_input = link / 'tests/fixtures/hand_adapter/raise_scenario.json'
        result, root, _, _ = self.invoke(extra=('--scenario', str(linked_input)))
        self.refused(result, root, pre_run=True)
        self.assertEqual(scenario.read_bytes(), (FIXTURES / 'raise_scenario.json').read_bytes())


    def test_input_hash_failures_precede_host_construction(self):
        for field in ('scenario', 'blueprint'):
            code = """import runpy, sys
from pathlib import Path
g = runpy.run_path('tools/v0a_hand_adapter.py')['main'].__globals__
root = Path(sys.argv[sys.argv.index('--run-root') + 1])
marker = root.parent / (root.name + '-constructed')
target = Path(sys.argv[sys.argv.index('--FIELD') + 1]).read_bytes()
original_hashlib, original_load = g['hashlib'], g['Source'].load
class HashFault:
    def sha256(self, raw=b''):
        if raw == target:
            raise MemoryError('controlled input hash failure')
        return original_hashlib.sha256(raw)
def load(source):
    modules = original_load(source)
    original_init = modules[2].ReplayHost.__init__
    def init(host, *args, **kwargs):
        marker.write_bytes(b'entered real host construction')
        return original_init(host, *args, **kwargs)
    modules[2].ReplayHost.__init__ = init
    return modules
g['hashlib'], g['Source'].load = HashFault(), load
raise SystemExit(g['main']())
""".replace('--FIELD', '--' + field)
            with self.subTest(field=field):
                result, root, _, _ = self.invoke(code=code)
                self.refused(result, root, pre_run=True)
                self.assertIn(b'controlled input hash failure', result.stderr)
                self.assertFalse((self.directory / (root.name + '-constructed')).exists())

    def test_terminal_output_success_short_write_and_failures(self):
        for schedule in ('post-flush', 'fileno', 'write-error', 'short-write'):
            fault = """base_stdout, real_os = sys.stdout, g['os']
attempt = path.parent.parent / (path.parent.name + '-output-attempt')
schedule = 'SCHEDULE'
class OutputOS:
    def __getattr__(self, name):
        return getattr(real_os, name)
    def write(self, descriptor, raw):
        attempt.write_text(schedule)
        if schedule == 'write-error':
            raise OSError('controlled stdout write failure')
        return real_os.write(descriptor, raw[:-1] if schedule == 'short-write' else raw)
class BufferFault:
    def write(self, raw):
        count = base_stdout.buffer.write(raw)
        base_stdout.buffer.flush()
        return count
    def flush(self):
        attempt.write_text('post-flush-fired')
        raise OSError('controlled post-publication flush failure')
class OutputStream:
    buffer = BufferFault()
    def fileno(self):
        if schedule == 'fileno':
            attempt.write_text(schedule)
            raise OSError('controlled stdout descriptor failure')
        return base_stdout.fileno()
    def flush(self):
        return base_stdout.flush()
g['os'], sys.stdout = OutputOS(), OutputStream()
""".replace('SCHEDULE', schedule)
            with self.subTest(schedule=schedule):
                result, root, _, _ = self.invoke(code=self.instrument(fault))
                if schedule == 'post-flush':
                    self.accepted(result, root)
                else:
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn(b'REFUSED', result.stderr)
                    self.assertNotIn(b'\n', result.stdout)
                    self.assertEqual(bool(result.stdout), schedule == 'short-write')
                attempt = self.directory / (root.name + '-output-attempt')
                self.assertEqual(attempt.read_text(), schedule)
                audit = json.loads((self.directory / (root.name + '-audit.json')).read_bytes())
                self.assertIs(audit['host_passed'], True)
                self.assertEqual(audit['accepted'], 1)
                self.assertEqual(audit['retained_sha256'],
                                 hashlib.sha256((root / 'trace.jsonl').read_bytes()).hexdigest())


if __name__ == '__main__':
    unittest.main()
