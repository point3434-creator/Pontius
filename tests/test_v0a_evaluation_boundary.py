"""Finite real boundary controls; synthetic publications are not engine results."""
import copy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

ROOT = Path.cwd()
TOOL = ROOT / 'tools/v0a_evaluation.py'


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RegistrationBoundaryTests(unittest.TestCase):
    def test_exact_loader_and_import_controls(self):
        checker = load(ROOT / 'tools/check_stabilization_boundaries.py', 'evaluation_boundaries')
        policy = getattr(checker, 'enforce_evaluation_import_policy', None)
        self.assertTrue(callable(policy), 'Exact evaluation registration policy is absent')
        wrapper, helper = 'tools/v0a_evaluation.py', 'tools/v0a_evaluation_contract.py'
        sources = {p: (ROOT / p).read_bytes() for p in (wrapper, helper)}
        policy(sources)
        variants = [
            (helper, b'\nimport subprocess\n', None),
            (wrapper, b'\nimport pontius\n', None),
            (wrapper, b"\nexec('pass')\n", None),
            (wrapper, b'\nhost.Source()\n', None),
            (wrapper, b'\nhost.Table()\n', None),
            (wrapper, b'\nhost.Session()\n', None),
            (wrapper, b'_pontius_evaluation_dealer', b'_evaluation_other_dealer'),
            (wrapper, b'(NEW[1], OLD[5], OLD[3])', b'(NEW[1], OLD[4], OLD[3])'),
            (wrapper, b'compile(s.raw[path],', b'compile(path.read_bytes(),'),
        ]
        for index, (path, before, after) in enumerate(variants):
            with self.subTest(variant=index):
                changed = dict(sources)
                if after is None:
                    changed[path] += before
                else:
                    self.assertIn(before, changed[path])
                    changed[path] = changed[path].replace(before, after)
                with self.assertRaises(checker.BoundaryError):
                    policy(changed)



class BoundaryTests(unittest.TestCase):
    def setUp(self):
        self.r = load(TOOL, 'evaluation_boundary_control')
        for alias in self.r.ALIASES:
            sys.modules.pop(alias, None)
        self.source = self.r.admit_source(ROOT)
        self.base = Path(tempfile.mkdtemp(prefix='ev-boundary-'))
        self.fixture = json.loads((ROOT / 'tests/fixtures/evaluation/controls.json').read_bytes())

    def publication(self):
        # Independent publication records only: no session report or engine is fabricated.
        r = self.r
        root = self.base / ('publication-%d' % len(list(self.base.iterdir())))
        root.mkdir()
        request = dict(version=r.PREFIX+'request-v1', seed='0'*64, deal_count=1,
            lineups=[['passive']*5], seat_start=0, initial_button=0,
            trial_budget_ms=1000, total_budget_ms=6000)
        saved = {root/'request.json': r.create_file(root/'request.json', r.encode(request))}
        plan = dict(version=r.PREFIX+'plan-v1', request_sha256=r.sha(r.encode(request)),
            source_commit=self.source.commit, source_manifest_sha256=self.source.manifest,
            blueprint_artifact_sha256=r.sha(self.source.raw[r.BLUEPRINT]), pairs=[], units=[])
        trials, pairs = [], []
        baseline, blueprint = [3, 5, 7, 11, 13, 17], [1, 2, 3, 5, 8, 13]
        for p in range(6):
            plan['pairs'].append(dict(pair_index=p, deal_index=0, lineup_index=0, rotation=p,
                controlled_seat=p, button=0, input_path='pairs/p%03d.json' % p,
                input_sha256='0'*64))
            for a in range(2):
                base = a == p % 2
                strategy = 'baseline-rules-v1' if base else 'blueprint-v1'
                ordinal = 2*p+a+1
                plan['units'].append(dict(ordinal=ordinal, pair_index=p, strategy=strategy,
                    session_id='pontius-v0a-table-session-v%d-correctness-eval-pub-u%03d' %
                               (2 if base else 1, ordinal),
                    input_path='pairs/p%03d.json' % p, input_sha256='0'*64))
                trials.append(dict(ordinal=ordinal, pair_index=p, strategy=strategy,
                    state='completed', exit_code=0, capture_complete=True, report_complete=True,
                    observation_complete=True, net_chips=(baseline if base else blueprint)[p],
                    applied_actions_by_kind={}, baseline_fallback_selections={} if base else None,
                    baseline_fallback_applied={} if base else None,
                    legacy_choices=None if base else {},
                    unattributed_applied_actions=0, work_cutoff_actions=0,
                    action_deadline_actions=0,
                    action_failures=[], failure_reason=None, hand_failure_codes=[],
                    session_failure_codes=[], capture_deficiencies=[], stdout_sha256='0'*64,
                    stderr_sha256='0'*64))
            pairs.append(dict(pair_index=p, complete=True, baseline_net_chips=baseline[p],
                blueprint_net_chips=blueprint[p], delta_chips=baseline[p]-blueprint[p]))
        aggregate = dict(baseline_net_chips=56, blueprint_net_chips=32, delta_chips=24,
                        mean_delta_numerator=24, mean_delta_denominator=6)
        aggregate['by_lineup'] = [dict(aggregate, lineup_index=0)]
        aggregate['by_seat'] = [dict(controlled_seat=p, baseline_net_chips=baseline[p],
            blueprint_net_chips=blueprint[p], delta_chips=baseline[p]-blueprint[p],
            mean_delta_numerator=baseline[p]-blueprint[p], mean_delta_denominator=1)
            for p in range(6)]
        saved[root/'plan.json'] = r.create_file(root/'plan.json', r.encode(plan))
        result = dict(version=r.PREFIX+'result-v1',
            evaluation_id='pontius-v0a-evaluation-v1-correctness-pub', status='completed',
            comparison_complete=True, source_commit=self.source.commit,
            source_manifest_sha256=self.source.manifest, request_sha256=plan['request_sha256'],
            plan_sha256=r.sha(r.encode(plan)), planned_pairs=6, completed_pairs=6,
            planned_trials=12, completed_trials=12, trials=trials, pairs=pairs,
            aggregate=aggregate, failure_reason=None, secondary_failures=[],
            total_elapsed_ns=0, deadline_met=True, evidentiary=False)
        return root, result, dict(source=self.source, saved=saved)

    def refused(self, root):
        self.assertTrue((root/'.publication-pending').exists())
        with self.assertRaisesRegex(ValueError, 'publication_pending'):
            self.r.read_completed(root)


    def test_normal_and_final_clock_edges(self):
        for final in (100, 101):
            with self.subTest(final=final):
                root, result, binding = self.publication()
                with patch.object(self.r, 'clock_ns', side_effect=[0, final]):
                    if final == 100:
                        self.r.publish(root, result, binding, 0, 100)
                        actual = self.r.read_completed(root)
                        self.assertEqual(actual, result)
                        self.assertEqual(actual['aggregate']['delta_chips'], 24)
                        self.assertEqual(actual['aggregate']['mean_delta_denominator'], 6)
                    else:
                        with self.assertRaisesRegex(ValueError, 'publication_late'):
                            self.r.publish(root, result, binding, 0, 100)
                        self.refused(root)
                        self.assertEqual(json.loads((root/'completion.json').read_bytes())[
                            'prepared_elapsed_ns'], 0)
                self.assertEqual((root/'result.json').read_bytes(), self.r.encode(result))

    def file_fault(self, filename, mode):
        root, result, binding = self.publication()
        target = root/filename
        real_open, real_rmdir, events, releases = Path.open, Path.rmdir, [], []
        now = [0]
        class Stream:
            def __init__(self, stream):
                self.stream = stream
            def __enter__(self):
                return self
            def write(self, raw):
                if mode in ('short', 'partial_error', 'partial_interrupt'):
                    count = self.stream.write(raw[:17])
                    events.append('partial_written')
                    if mode != 'short':
                        error = KeyboardInterrupt if mode == 'partial_interrupt' else OSError
                        raise error('fault')
                    return count
                count = self.stream.write(raw)
                events.append('full_written')
                if mode == 'write_late':
                    now[0] = 101
                return count
            def flush(self):
                self.stream.flush()
                events.append('flushed')
                if mode == 'flush':
                    raise OSError('flush fault')
            def fileno(self):
                return self.stream.fileno()
            def __exit__(self, *args):
                self.stream.close()
                events.append('closed')
                if mode == 'close_late':
                    now[0] = 101
                if mode in ('close', 'close_interrupt'):
                    error = KeyboardInterrupt if mode == 'close_interrupt' else OSError
                    raise error('close fault')
                if mode == 'readback':
                    with real_open(target, 'r+b') as stream:
                        stream.write(b'!')
                    events.append('corrupted')
        def opened(path, *args, **kwargs):
            stream = real_open(path, *args, **kwargs)
            return Stream(stream) if path == target and args == ('xb',) else stream
        def release(path):
            releases.append(path)
            return real_rmdir(path)
        with patch.object(Path, 'open', opened), patch.object(Path, 'rmdir', release), \
                patch.object(self.r, 'clock_ns', lambda: now[0]):
            with self.assertRaises((ValueError, OSError, KeyboardInterrupt)):
                self.r.publish(root, result, binding, 0, 100)
        self.assertIn('closed', events, 'Fault must reach a real file and real close')
        self.assertEqual(releases, [])
        raw = target.read_bytes()
        self.assertTrue(raw)
        if mode.startswith('partial') or mode == 'short':
            self.assertEqual(len(raw), 17)
        elif mode != 'readback':
            self.assertIs(type(json.loads(raw)), dict)
        self.refused(root)
        before = {p.name: p.read_bytes() for p in root.iterdir() if p.is_file()}
        with self.assertRaises(FileExistsError):
            self.r.publish(root, result, binding, 0, 100)
        self.assertEqual(before, {p.name: p.read_bytes() for p in root.iterdir() if p.is_file()})

    def test_result_write_flush_close_readback_faults(self):
        for mode in ('short', 'flush', 'close', 'readback'):
            with self.subTest(mode=mode):
                self.file_fault('result.json', mode)

    def test_completion_faults_partial_interrupt_and_actual_delays(self):
        for mode in ('short', 'flush', 'close', 'readback', 'partial_error',
                     'partial_interrupt', 'close_interrupt', 'write_late', 'close_late'):
            with self.subTest(mode=mode):
                self.file_fault('completion.json', mode)

    def test_fsync_and_final_file_collision_preserve_guard(self):
        for filename in ('result.json', 'completion.json'):
            with self.subTest(filename=filename):
                root, result, binding = self.publication()
                (root/filename).write_bytes(b'prior file\n')
                with self.assertRaises(FileExistsError):
                    self.r.publish(root, result, binding, 0, 100)
                self.assertEqual((root/filename).read_bytes(), b'prior file\n')
                self.refused(root)
        for selected in (1, 2):
            with self.subTest(fsync_call=selected):
                root, result, binding = self.publication()
                original, real_rmdir, calls, releases = os.fsync, Path.rmdir, [], []
                def fail(fd):
                    original(fd)
                    calls.append(fd)
                    if len(calls) == selected:
                        raise OSError('after actual fsync')
                def release(path):
                    releases.append(path)
                    return real_rmdir(path)
                with patch.object(os, 'fsync', fail), patch.object(Path, 'rmdir', release), \
                        patch.object(self.r, 'clock_ns', return_value=0):
                    with self.assertRaises(OSError):
                        self.r.publish(root, result, binding, 0, 100)
                self.assertEqual(len(calls), selected)
                self.assertEqual(releases, [])
                self.assertEqual(json.loads((root/'result.json').read_bytes()), result)
                if selected == 2:
                    self.assertEqual(json.loads((root/'completion.json').read_bytes())[
                        'result_sha256'], self.r.sha(self.r.encode(result)))
                self.refused(root)

    def test_release_delay_failure_and_ambiguity(self):
        for mode in ('late', 'failed', 'interrupted', 'ambiguous', 'ambiguous_interrupt'):
            with self.subTest(mode=mode):
                root, result, binding = self.publication()
                real, attempts, now = Path.rmdir, [], [0]
                def release(path):
                    self.assertEqual(path, root/'.publication-pending')
                    attempts.append(path)
                    now[0] = 101
                    if mode not in ('failed', 'interrupted'):
                        real(path)
                    if mode != 'late':
                        error = KeyboardInterrupt if 'interrupt' in mode else OSError
                        raise error('release fault')
                with patch.object(Path, 'rmdir', release), \
                        patch.object(self.r, 'clock_ns', lambda: now[0]):
                    if mode == 'late':
                        self.r.publish(root, result, binding, 0, 100)
                    else:
                        with self.assertRaises((OSError, KeyboardInterrupt)):
                            self.r.publish(root, result, binding, 0, 100)
                self.assertEqual(len(attempts), 1)
                if mode in ('failed', 'interrupted'):
                    self.refused(root)
                else:
                    self.assertFalse((root/'.publication-pending').exists())
                    self.assertEqual(self.r.read_completed(root), result)

    def test_revalidation_rejects_actual_saved_file_drift(self):
        for filename in ('request.json', 'plan.json', 'result.json', 'completion.json'):
            with self.subTest(filename=filename):
                root, result, binding = self.publication()
                original, fired = self.r.revalidate, []
                def drift(value):
                    path = root/filename
                    (root/(filename+'.preserved')).write_bytes(path.read_bytes())
                    with path.open('ab') as stream:
                        stream.write(b' ')
                    fired.append(path)
                    return original(value)
                with patch.object(self.r, 'revalidate', drift), \
                        patch.object(self.r, 'clock_ns', return_value=0):
                    with self.assertRaises(ValueError):
                        self.r.publish(root, result, binding, 0, 100)
                self.assertEqual(len(fired), 1)
                self.refused(root)

    def test_reader_rechecks_actual_guard_and_file_identity(self):
        for mode in ('guard', 'identity'):
            with self.subTest(mode=mode):
                root, result, binding = self.publication()
                with patch.object(self.r, 'clock_ns', return_value=0):
                    self.r.publish(root, result, binding, 0, 100)
                original, fired = self.r.read_stable, []
                def read(path, *args, **kwargs):
                    saved = original(path, *args, **kwargs)
                    if path == root/'plan.json' and not fired:
                        fired.append(path)
                        if mode == 'guard':
                            (root/'.publication-pending').write_bytes(b'guard object')
                        else:
                            target = root/'result.json'
                            target.rename(root/'preserved-result.json')
                            target.write_bytes((root/'preserved-result.json').read_bytes())
                    return saved
                with patch.object(self.r, 'read_stable', read):
                    with self.assertRaises(ValueError):
                        self.r.read_completed(root)
                self.assertEqual(len(fired), 1)

    def test_total_deadline_covers_real_reduction(self):
        root, result, binding = self.publication()
        plan = json.loads((root/'plan.json').read_bytes())
        reduced = self.source.contract.reduce_trials(plan, result['trials'])
        self.assertEqual(reduced, {k: result[k] for k in ('pairs', 'aggregate')})
        # Only the clock trigger changes after real reduction; result rows stay synthetic.
        with patch.object(self.r, 'clock_ns', return_value=101):
            with self.assertRaisesRegex(ValueError, 'publication_late'):
                self.r.publish(root, result, binding, 0, 100)
        self.refused(root)

    def test_missing_final_clock_mutant_breaks_independent_oracle(self):
        import ast
        tree = ast.parse(TOOL.read_bytes())
        function = next(n for n in tree.body if isinstance(n, ast.FunctionDef)
                        and n.name == 'publish')
        removed = [n for n in function.body if isinstance(n, ast.Expr) and
                   isinstance(n.value, ast.Call) and isinstance(n.value.func, ast.Name) and
                   n.value.func.id == 'require']
        self.assertEqual(len(removed), 1)
        function.body.remove(removed[0])
        mutant = ast.Module(body=[function], type_ignores=[])
        raw = ast.unparse(mutant).encode() + b'\n'
        (self.base/'late-publication-mutant.py').write_bytes(raw)
        namespace = dict(vars(self.r))
        exec(compile(mutant, str(self.base/'late-publication-mutant.py'), 'exec'), namespace)
        namespace['clock_ns'] = lambda: 101
        root, result, binding = self.publication()
        namespace['publish'](root, result, binding, 0, 100)
        with self.assertRaises(AssertionError):
            with self.assertRaises(ValueError, msg='Late precommit must never be consumable'):
                self.r.read_completed(root)
        self.assertEqual(self.r.read_completed(root), result)


    def test_preloaded_modules_and_changed_helper_identity_refuse(self):
        for alias in self.r.ALIASES:
            sys.modules.pop(alias, None)
        for name in ('pontius', 'pontius.child', *self.r.ALIASES):
            with self.subTest(name=name):
                with patch.dict(sys.modules, {name: object()}):
                    with self.assertRaisesRegex(ValueError, 'source_invalid'):
                        self.r.admit_source(ROOT)
        sys.modules.update(self.source.modules)
        for name in self.r.ALIASES:
            with self.subTest(alias=name), patch.dict(sys.modules, {name: object()}):
                with self.assertRaisesRegex(ValueError, 'source_invalid'):
                    self.source.check()
        with patch.object(self.source.host, '__file__', str(ROOT/'tools/wrong.py')):
            with self.assertRaisesRegex(ValueError, 'source_invalid'):
                self.source.check()

    def test_wrong_interpreter_flags_and_git_refuse_without_root(self):
        request, output = self.base/'request.json', self.base/'out'
        request.write_bytes(b'{}\n')
        tail = [str(TOOL), '--request', str(request), '--output-root', str(output),
                '--evaluation-id', 'pontius-v0a-evaluation-v1-correctness-invalid']
        for flags in (['-P'], ['-B']):
            with self.subTest(flags=flags):
                process = subprocess.run([sys.executable, *flags, *tail], capture_output=True,
                                         timeout=30)
                self.assertEqual(process.returncode, 1, process.stderr)
                self.assertFalse(output.exists())
        for value in ('relative-git.exe', str(self.base/'missing.exe')):
            with self.subTest(git=value), patch.dict(os.environ, {'PONTIUS_GIT': value}):
                for alias in self.r.ALIASES:
                    sys.modules.pop(alias, None)
                with self.assertRaises((ValueError, OSError)):
                    self.r.admit_source(ROOT)
                self.assertFalse(output.exists())
        with patch.object(self.r, '__file__', str(ROOT/'wrong.py')):
            with self.assertRaises(ValueError):
                self.r.admit_source(ROOT)

    def test_raw_source_new_tool_missing_helper_and_extra_paths_refuse(self):
        faults = [('src/pontius/__init__.py', 'append'),
                  ('tools/v0a_evaluation_contract.py', 'append'),
                  ('tools/v0a_seeded_deals.py', 'missing'),
                  ('src/pontius/extra_boundary.py', 'extra'),
                  ('src/pontius/extra_boundary', 'directory')]
        for index, (name, mode) in enumerate(faults):
            with self.subTest(path=name, mode=mode):
                clone = self.base/('source-%d' % index)
                env = dict(self.source.env, PONTIUS_GIT=str(self.source.git))
                for args in (['clone', '--quiet', '--no-hardlinks', '--no-checkout',
                              str(ROOT), str(clone)],
                             ['-C', str(clone), '-c', 'core.autocrlf=false',
                              'checkout', '--quiet', '--detach', self.source.commit]):
                    process = subprocess.run([str(self.source.git), '--no-replace-objects',
                        *args], env=env, capture_output=True, timeout=60)
                    self.assertEqual(process.returncode, 0, process.stderr)
                target = clone/name
                if target.is_file():
                    preserved = self.base/('original-%d.bin' % index)
                    preserved.write_bytes(target.read_bytes())
                if mode == 'append':
                    with target.open('ab') as stream:
                        stream.write(b'\n# finite source drift\n')
                elif mode == 'missing':
                    target.rename(self.base/('missing-helper-%d.py' % index))
                elif mode == 'extra':
                    target.write_bytes(b'# extra source\n')
                else:
                    target.mkdir()
                runner = load(clone/'tools/v0a_evaluation.py', 'source_boundary_%d' % index)
                for alias in runner.ALIASES:
                    sys.modules.pop(alias, None)
                previous = Path.cwd()
                try:
                    os.chdir(clone)
                    with self.assertRaises((ValueError, OSError)):
                        runner.admit_source(clone)
                    self.assertFalse(any(alias in sys.modules for alias in runner.ALIASES))
                finally:
                    os.chdir(previous)

    def test_root_and_guard_object_collisions_preserve_prior_owner(self):
        request, output = self.base/'request.json', self.base/'out'
        request.write_bytes(b'{}\n')
        output.mkdir()
        sentinel = output/'reservation.json'
        sentinel.write_bytes(b'prior reservation\n')
        args = types.SimpleNamespace(request=request, output_root=output,
            evaluation_id='pontius-v0a-evaluation-v1-correctness-collision')
        with self.assertRaises(FileExistsError):
            self.r.execute(args, self.source)
        self.assertEqual(list(output.iterdir()), [sentinel])
        self.assertEqual(sentinel.read_bytes(), b'prior reservation\n')
        root, result, binding = self.publication()
        (root/'.publication-pending').write_bytes(b'prior guard object')
        with self.assertRaises(FileExistsError):
            self.r.publish(root, result, binding, 0, 100)
        self.assertEqual((root/'.publication-pending').read_bytes(), b'prior guard object')
        self.assertFalse((root/'result.json').exists())
        self.refused(root)


    def unit(self):
        base = self.base/('unit-%d' % len(list(self.base.iterdir())))
        base.mkdir()
        matrix = self.source.contract.build_matrix(self.fixture['request'],
                                                   self.fixture['deals'], 'boundary')
        pair, unit = matrix['pairs'][0], matrix['units'][0]
        path = base/'pair.json'
        path.write_bytes(pair['input_bytes'])
        root, temp = base/'u001', base/'temp'
        root.mkdir()
        temp.mkdir()
        binding = dict(self.fixture['binding'], **unit, source=self.source,
            source_commit=self.source.commit, source_manifest_sha256=self.source.manifest,
            child_source_manifest_sha256=self.source.child_manifest, request_sha256='0'*64,
            trial_budget_ms=30000, saved={path: self.r.read_stable(path)})
        return base, binding, dict(root=root, temp=temp, input=path)

    def test_whole_trial_exact_fit_one_ns_short_and_revalidation_delay(self):
        for mode in ('fit', 'short', 'revalidation_delay'):
            with self.subTest(mode=mode):
                base, binding, paths = self.unit()
                binding['trial_budget_ms'] = 1000
                marker = base/'executed'
                code = 'from pathlib import Path; Path(%r).write_bytes(b"ran")' % str(marker)
                now, checks = [0], []
                original = self.r.revalidate
                def checked(value):
                    original(value)
                    checks.append(1)
                    if mode == 'revalidation_delay':
                        now[0] = 1
                with patch.object(self.r, 'clock_ns', lambda: now[0]), \
                        patch.object(self.r, 'revalidate', checked), \
                        patch.object(self.r, 'child_argv', return_value=[
                            sys.executable, '-B', '-P', '-c', code]):
                    outcome = self.r.run_trial(binding, paths,
                        6000000000 - (1 if mode == 'short' else 0))
                self.assertIsNone(outcome['net_chips'])
                if mode == 'fit':
                    self.assertEqual(marker.read_bytes(), b'ran')
                    self.assertTrue(outcome['launched'])
                    self.assertTrue(outcome['cleanup_complete'])
                else:
                    self.assertFalse(marker.exists())
                    self.assertFalse((paths['root']/'intent.json').exists())
                    self.assertEqual(outcome['failure_reason'], 'budget_insufficient')
                self.assertEqual(json.loads((paths['root']/'result.json').read_bytes()), outcome)

    def test_saved_inputs_drift_before_trial_prevents_child(self):
        for filename in ('original-request.json', 'request.json', 'plan.json', 'pair.json'):
            with self.subTest(filename=filename):
                base, binding, paths = self.unit()
                path = base/filename
                if not path.exists():
                    path.write_bytes(b'{}\n')
                binding['saved'][path] = self.r.read_stable(path)
                (base/(filename+'.preserved')).write_bytes(path.read_bytes())
                with path.open('ab') as stream:
                    stream.write(b' ')
                marker = base/'executed'
                argv = [sys.executable, '-B', '-P', '-c',
                        'from pathlib import Path; Path(%r).touch()' % str(marker)]
                with patch.object(self.r, 'child_argv', return_value=argv):
                    outcome = self.r.run_trial(binding, paths, self.r.clock_ns()+60000000000)
                self.assertEqual(outcome['failure_reason'], 'input_invalid')
                self.assertIsNone(outcome['net_chips'])
                self.assertFalse(marker.exists())
                self.assertFalse((paths['root']/'intent.json').exists())

    def test_actual_child_drift_keeps_prefix_and_stops_later_units(self):
        for filename in ('original', 'request.json', 'plan.json', 'pairs/p000.json'):
            with self.subTest(filename=filename):
                base = self.base/('execute-%d' % len(list(self.base.iterdir())))
                base.mkdir()
                request, output, marker = base/'request.json', base/'out', base/'executed'
                value = dict(self.fixture['request'], deal_count=1, lineups=[['passive']*5],
                             trial_budget_ms=30000, total_budget_ms=60000)
                request.write_bytes(self.r.encode(value))
                target = request if filename == 'original' else output/filename
                code = ('from pathlib import Path; import os; '
                    'Path(%r).write_bytes(Path(%r).read_bytes()); '
                    'f=Path(%r).open("ab"); f.write(b" "); f.close(); '
                    'Path(%r).write_bytes(b"ran"); os.write(1,b"{prefix")') % (
                        str(base/'original-bytes'), str(target), str(target), str(marker))
                def literal(seed, index):
                    self.assertEqual(index, 0)
                    return copy.deepcopy(self.fixture['deals'][0])
                args = types.SimpleNamespace(request=request, output_root=output,
                    evaluation_id='pontius-v0a-evaluation-v1-correctness-drift')
                with patch.object(self.source.dealer, 'deal_for_hand', literal), \
                        patch.object(self.r, 'child_argv', return_value=[
                            sys.executable, '-B', '-P', '-c', code]):
                    self.assertEqual(self.r.execute(args, self.source), 1)
                self.assertEqual(marker.read_bytes(), b'ran')
                self.assertEqual((output/'u001/stdout.bin').read_bytes(), b'{prefix')
                outcome = json.loads((output/'u001/result.json').read_bytes())
                result = json.loads((output/'result.json').read_bytes())
                self.assertEqual(outcome['failure_reason'], 'input_invalid')
                self.assertTrue(outcome['launched'] and outcome['cleanup_complete'])
                self.assertEqual([r['state'] for r in result['trials'][1:]], ['unstarted']*11)
                self.assertEqual([p.name for p in output.glob('u*')], ['u001'])
                self.assertFalse(result['trials'][0]['report_complete'])
                self.assertFalse(result['trials'][0]['observation_complete'])
                self.assertIsNone(result['trials'][0]['net_chips'])
                self.assertIsNone(result['aggregate'])
                self.refused(output)

    def test_child_environment_drops_finite_poison_values(self):
        base, binding, paths = self.unit()
        marker = base/'environment.json'
        code = ('import os,json; from pathlib import Path; '
                'Path(%r).write_text(json.dumps(dict(os.environ)))') % str(marker)
        poison = dict(GIT_DIR='wrong', GIT_CONFIG_COUNT='1', GIT_CONFIG_KEY_0='alias.bad',
            GIT_CONFIG_VALUE_0='bad', PYTHONSTARTUP='wrong', PYTHONPATH='wrong',
            PONTIUS_BOUNDARY_POISON='wrong')
        with patch.dict(os.environ, poison), patch.object(self.r, 'child_argv', return_value=[
                sys.executable, '-B', '-P', '-c', code]):
            outcome = self.r.run_trial(binding, paths, self.r.clock_ns()+60000000000)
        self.assertTrue(outcome['launched'] and outcome['cleanup_complete'])
        environment = json.loads(marker.read_bytes())
        expected = self.r.child_environment(self.source, paths['temp'])
        self.assertEqual({k.upper(): v for k, v in environment.items()},
                         {k.upper(): v for k, v in expected.items()})
        self.assertEqual(environment['PYTHONPATH'], str(ROOT/'src'))
        self.assertFalse(set(poison)-{'PYTHONPATH'} & set(environment))

    def test_real_source_drift_after_child_and_before_publication_refuses(self):
        clone = self.base/'source'
        for args in (['clone', '--quiet', '--no-hardlinks', '--no-checkout', str(ROOT), str(clone)],
                     ['-C', str(clone), '-c', 'core.autocrlf=false', 'checkout', '--quiet',
                      '--detach', self.source.commit]):
            process = subprocess.run([str(self.source.git), '--no-replace-objects', *args],
                                     env=self.source.env, capture_output=True, timeout=60)
            self.assertEqual(process.returncode, 0, process.stderr)
        runner = load(clone/'tools/v0a_evaluation.py', 'post_child_source_boundary')
        for alias in runner.ALIASES:
            sys.modules.pop(alias, None)
        previous = Path.cwd()
        try:
            os.chdir(clone)
            self.source = runner.admit_source(clone)
        finally:
            os.chdir(previous)
        base, binding, paths = self.unit()
        source_path, marker = clone/'src/pontius/__init__.py', base/'executed'
        preserved = base/'original-source.py'
        preserved.write_bytes(source_path.read_bytes())
        code = ('from pathlib import Path; import os; f=Path(%r).open("ab"); '
                'f.write(b"\\n# source fault\\n"); f.close(); '
                'Path(%r).write_bytes(b"ran"); os.write(1,b"{source-prefix")') % (
                    str(source_path), str(marker))
        with patch.object(self.r, 'child_argv', return_value=[
                sys.executable, '-B', '-P', '-c', code]):
            outcome = self.r.run_trial(binding, paths, self.r.clock_ns()+60000000000)
        self.assertEqual(marker.read_bytes(), b'ran')
        self.assertEqual((paths['root']/'stdout.bin').read_bytes(), b'{source-prefix')
        self.assertEqual(outcome['failure_reason'], 'source_invalid')
        self.assertTrue(outcome['launched'] and outcome['cleanup_complete'])
        self.assertIsNone(outcome['net_chips'])
        self.assertNotEqual(source_path.read_bytes(), preserved.read_bytes())
        root, result, publication_binding = self.publication()
        with patch.object(self.r, 'clock_ns', return_value=0):
            with self.assertRaisesRegex(ValueError, 'source_invalid'):
                self.r.publish(root, result, publication_binding, 0, 100)
        self.assertIs(type(json.loads((root/'completion.json').read_bytes())), dict)
        self.refused(root)

if __name__ == '__main__':
    unittest.main()
