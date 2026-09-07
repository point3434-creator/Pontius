"""Finite retained runner controls; no evaluation authority or population tuning."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path.cwd()
TOOL = ROOT / 'tools/v0a_evaluation.py'


def load():
    spec = importlib.util.spec_from_file_location('evaluation_runner_control', TOOL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class AdmissionTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(TOOL.is_file(), 'The accepted evaluation runner is absent')
        self.runner = load()
        for alias in self.runner.ALIASES:
            sys.modules.pop(alias, None)

    def test_admit_exact_source_without_poker_imports(self):
        source = self.runner.admit_source(ROOT)
        self.assertFalse(any(n == 'pontius' or n.startswith('pontius.') for n in sys.modules))
        rows = [hashlib.sha256(raw).hexdigest().encode() + b'  ' + p.encode() + b'\n'
                for p, raw in source.raw.items()]
        self.assertEqual(source.manifest, hashlib.sha256(b''.join(sorted(rows))).hexdigest())
        self.assertNotEqual(source.manifest, source.child_manifest)
        self.assertEqual(set(self.runner.ALIASES), {n for n in sys.modules
                         if n.startswith('_pontius_evaluation_')})
        source.check()

    def test_existing_output_root_refuses_without_overwrite(self):
        base = Path(tempfile.mkdtemp(prefix='ev-admit-'))
        request = base / 'request.json'
        request.write_bytes(b'{}\n')
        output = base / 'consumed'
        output.mkdir()
        sentinel = output / 'reservation.json'
        sentinel.write_bytes(b'prior owner\n')
        result = self.runner.main(['--request', str(request), '--output-root', str(output),
                                  '--evaluation-id', 'pontius-v0a-evaluation-v1-correctness-root'])
        self.assertEqual(result, 1)
        self.assertEqual(sentinel.read_bytes(), b'prior owner\n')
        self.assertEqual(list(output.iterdir()), [sentinel])

    def test_cli_parse_error_uses_failure_exit(self):
        process = subprocess.run([sys.executable, '-B', '-P', str(TOOL), '--unknown'],
                                 capture_output=True, timeout=10)
        self.assertEqual(process.returncode, 1, process.stderr)
        help_result = subprocess.run([sys.executable, '-B', '-P', str(TOOL), '--help'],
                                     capture_output=True, timeout=10)
        self.assertEqual(help_result.returncode, 0, help_result.stderr)
    def test_preloaded_alias_refuses(self):
        sys.modules[self.runner.ALIASES[0]] = object()
        with self.assertRaisesRegex(ValueError, 'source_invalid'):
            self.runner.admit_source(ROOT)



    def test_ancestor_replacement_changes_stable_read_identity(self):
        base = Path(tempfile.mkdtemp(prefix='ev-ancestor-'))
        parent, preserved = base / 'parent', base / 'preserved'
        parent.mkdir()
        path = parent / 'input.json'
        path.write_bytes(b'{}\n')
        before = self.runner.read_stable(path)
        # Replace an unconsumed fixture ancestor, preserving both directories and file bytes.
        parent.rename(preserved)
        parent.mkdir()
        os.link(preserved / 'input.json', path)
        self.assertEqual(path.stat().st_ino, (preserved / 'input.json').stat().st_ino)
        self.assertNotEqual(self.runner.read_stable(path), before)

    def test_non_native_git_refuses_before_first_git_command(self):
        base = Path(tempfile.mkdtemp(prefix='ev-native-git-'))
        path = base / 'git.cmd'
        path.write_bytes(b'@exit /b 1\r\n')
        previous = os.environ['PONTIUS_GIT']
        os.environ['PONTIUS_GIT'] = str(path)
        self.addCleanup(os.environ.__setitem__, 'PONTIUS_GIT', previous)
        original, calls = self.runner.SourceBinding.command, []
        def record(source, *args, **kwargs):
            calls.append(args)
            return original(source, *args, **kwargs)
        self.runner.SourceBinding.command = record
        with self.assertRaises((ValueError, OSError)):
            self.runner.admit_source(ROOT)
        self.assertEqual(calls, [], 'Non-native Git reached subprocess execution')

    def test_loaded_helper_origin_drift_refuses(self):
        source = self.runner.admit_source(ROOT)
        previous = source.host.__file__
        source.host.__file__ = str(ROOT / 'tools/wrong.py')
        self.addCleanup(setattr, source.host, '__file__', previous)
        with self.assertRaisesRegex(ValueError, 'source_invalid'):
            source.check()
class NativeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runner = load()
        for alias in cls.runner.ALIASES:
            sys.modules.pop(alias, None)
        cls.source = cls.runner.admit_source(ROOT)

    def setUp(self):
        self.assertTrue(callable(getattr(self.runner, 'run_trial', None)),
                        'The native trial boundary is absent')
        self.base = Path(tempfile.mkdtemp(prefix='ev-native-'))
        fixture = json.loads((ROOT / 'tests/fixtures/evaluation/controls.json').read_bytes())
        matrix = self.source.contract.build_matrix(fixture['request'], fixture['deals'], 'native')
        pair, unit = matrix['pairs'][0], matrix['units'][0]
        input_path = self.base / 'pair.json'
        input_path.write_bytes(pair['input_bytes'])
        self.unit_root = self.base / 'u001'
        self.unit_root.mkdir()
        temp = self.base / 'temp'
        temp.mkdir()
        self.paths = dict(root=self.unit_root, input=input_path, temp=temp)
        self.binding = dict(fixture['binding'], **unit, source=self.source,
            source_commit=self.source.commit, source_manifest_sha256=self.source.manifest,
            child_source_manifest_sha256=self.source.child_manifest,
            request_sha256='0' * 64, trial_budget_ms=60000,
            saved={input_path: self.runner.read_stable(input_path)})
        self.original_argv = self.runner.child_argv
        self.processes = []
        self.original_popen = self.runner.subprocess.Popen
        def launch(*args, **kwargs):
            p = self.original_popen(*args, **kwargs)
            if kwargs.get('creationflags', 0) & 4:
                self.processes.append(p)
            return p
        self.runner.subprocess.Popen = launch
        self.addCleanup(setattr, self.runner.subprocess, 'Popen', self.original_popen)
        self.addCleanup(setattr, self.runner, 'child_argv', self.original_argv)

    def worker(self, code):
        self.runner.child_argv = lambda binding, paths: [sys.executable, '-B', '-P', '-c', code]

    def trial(self):
        result = self.runner.run_trial(self.binding, self.paths,
                                      self.runner.clock_ns() + 120000000000)
        self.assertTrue((self.unit_root / 'intent.json').is_file())
        self.assertEqual(json.loads((self.unit_root / 'result.json').read_bytes()), result)
        self.assertNotEqual(result['state'], 'completed')
        self.assertIsNone(result['net_chips'])
        self.assertTrue(all(p.poll() is not None for p in self.processes))
        return result

    def test_partial_json_keeps_raw_capture_and_refuses_report(self):
        self.worker("import os; os.write(1,b'{\"version\":')")
        result = self.trial()
        self.assertEqual((self.unit_root / 'stdout.bin').read_bytes(), b'{"version":')
        self.assertTrue(result['capture_complete'])
        self.assertFalse(result['report_complete'])
        self.assertTrue(result['cleanup_complete'])
        self.assertTrue(result['launched'])

    def test_assignment_failure_never_executes_child(self):
        marker = self.base / 'executed'
        self.worker('from pathlib import Path; Path(' + repr(str(marker)) + ").write_text('ran')")
        original = self.source.host.Job.assign
        def refuse(job, process):
            raise ValueError('containment_failed')
        self.source.host.Job.assign = refuse
        self.addCleanup(setattr, self.source.host.Job, 'assign', original)
        result = self.trial()
        self.assertFalse(marker.exists())
        self.assertFalse((self.unit_root / 'launch.json').exists())
        self.assertIsNone(result['launched'])
        self.assertEqual(result['failure_reason'], 'containment_failed')
        self.assertTrue(result['cleanup_complete'])

    def test_stdout_overflow_is_capped_and_stopped(self):
        self.worker("import os,time; os.write(1,b'x'*4194305); time.sleep(60)")
        result = self.trial()
        self.assertEqual((self.unit_root / 'stdout.bin').stat().st_size, 4194304)
        self.assertFalse(result['capture_complete'])
        self.assertEqual(result['failure_reason'], 'stdout_overflow')
        self.assertTrue(result['cleanup_complete'])

    def test_stderr_overflow_is_capped_and_stopped(self):
        self.worker("import os,time; os.write(2,b'x'*65537); time.sleep(60)")
        result = self.trial()
        self.assertEqual((self.unit_root / 'stderr.bin').stat().st_size, 65536)
        self.assertFalse(result['capture_complete'])
        self.assertEqual(result['failure_reason'], 'stderr_overflow')
        self.assertTrue(result['cleanup_complete'])

    def test_expired_trial_admission_never_launches(self):
        self.binding['trial_budget_ms'] = 1
        marker = self.base / 'executed'
        self.worker('from pathlib import Path; Path(' + repr(str(marker)) + ").write_text('ran')")
        result = self.trial()
        self.assertEqual(result['failure_reason'], 'trial_timeout')
        self.assertEqual(self.processes, [], 'A child was created after the trial deadline')
        self.assertFalse(marker.exists())
    def test_timeout_stops_child(self):
        self.binding['trial_budget_ms'] = 5000
        self.worker('import time; time.sleep(60)')
        result = self.trial()
        self.assertEqual(result['failure_reason'], 'trial_timeout')
        self.assertTrue(result['cleanup_complete'])


    def test_intent_then_capture_failure_retains_unknown_launch(self):
        (self.unit_root / 'stdout.bin').write_bytes(b'collision')
        self.worker("raise AssertionError('must not run')")
        result = self.trial()
        self.assertIsNone(result['launched'])
        self.assertFalse((self.unit_root / 'launch.json').exists())
        self.assertEqual((self.unit_root / 'stdout.bin').read_bytes(), b'collision')

    def test_constructor_secondary_cleanup_failure_is_not_complete(self):
        original = self.source.host.Job
        observed = []
        def constructor():
            job = original()
            job.close()
            observed.append(job.handle)
            raise self.source.host.HostRefusal('containment_failed',
                                              secondary=('cleanup_failed',))
        self.source.host.Job = constructor
        self.addCleanup(setattr, self.source.host, 'Job', original)
        self.worker('pass')
        result = self.trial()
        self.assertEqual(observed, [None])
        self.assertEqual(self.processes, [])
        self.assertIn('cleanup_failed', result['secondary_failures'])
        self.assertFalse(result['cleanup_complete'])
    def test_creation_exception_keeps_cleanup_unknown(self):
        def failed_launch(*args, **kwargs):
            if kwargs.get('creationflags', 0) & 4:
                raise OSError('creation outcome unavailable')
            return self.original_popen(*args, **kwargs)
        self.runner.subprocess.Popen = failed_launch
        self.worker('pass')
        result = self.trial()
        self.assertIsNone(result['launched'])
        self.assertFalse(result['cleanup_complete'])

    def test_observation_finishes_after_trial_deadline(self):
        self.worker("import os; os.write(1,b'{}')")
        original_clock = self.runner.clock_ns
        original_observer = self.source.contract.observe_trial
        def delayed(*args, **kwargs):
            value = original_observer(*args, **kwargs)
            self.runner.clock_ns = lambda: original_clock() + 120000000000
            return value
        self.source.contract.observe_trial = delayed
        self.addCleanup(setattr, self.source.contract, 'observe_trial', original_observer)
        self.addCleanup(setattr, self.runner, 'clock_ns', original_clock)
        result = self.trial()
        self.assertEqual(result['failure_reason'], 'trial_timeout')

    def test_interrupt_after_real_resume_stops_child(self):
        self.worker('import time; time.sleep(60)')
        original = self.source.host.Job.resume
        def interrupted(job, process):
            original(job, process)
            raise KeyboardInterrupt()
        self.source.host.Job.resume = interrupted
        self.addCleanup(setattr, self.source.host.Job, 'resume', original)
        result = self.trial()
        self.assertEqual(result['state'], 'interrupted')
        self.assertIsNone(result['launched'])
        self.assertTrue(result['cleanup_complete'])

    def test_cleanup_refusal_is_retained_after_actual_close(self):
        self.worker("import os; os.write(1,b'{}')")
        original = self.source.host.Job.close
        def refused(job):
            original(job)
            raise ValueError('cleanup_failed')
        self.source.host.Job.close = refused
        self.addCleanup(setattr, self.source.host.Job, 'close', original)
        result = self.trial()
        self.assertFalse(result['cleanup_complete'])
        self.assertEqual(result['failure_reason'], 'cleanup_failed')

    def test_bypassing_assignment_fails_independent_marker_check(self):
        marker = self.base / 'executed'
        self.worker('from pathlib import Path; Path(' + repr(str(marker)) + ").write_text('ran')")
        original = self.source.host.Job.assign
        self.source.host.Job.assign = lambda job, process: None
        self.addCleanup(setattr, self.source.host.Job, 'assign', original)
        self.trial()
        with self.assertRaises(AssertionError):
            self.assertFalse(marker.exists(), 'Uncontained child executed before assignment')

    def test_overflow_stops_observed_native_descendant(self):
        self.descendant_control('stdout_overflow')

    def test_timeout_stops_observed_native_descendant(self):
        self.binding['trial_budget_ms'] = 10000
        self.descendant_control('trial_timeout')

    def descendant_control(self, cause):
        import ctypes
        import time
        pidfile, gate = self.base / 'pid', self.base / 'gate'
        code = ('import subprocess,sys,time,os; from pathlib import Path; '
            "p=subprocess.Popen([sys.executable,'-B','-P','-c','import time; time.sleep(60)']); "
            'Path(' + repr(str(pidfile)) + ').write_text(str(p.pid)); '
            '\nwhile not Path(' + repr(str(gate)) + ').exists(): time.sleep(.005)'
            "\nos.write(1,b'x'*4194305); time.sleep(60)")
        if cause == 'trial_timeout':
            code = code.replace("os.write(1,b'x'*4194305); ", '')
        self.worker(code)
        api = ctypes.WinDLL('kernel32', use_last_error=True)
        api.OpenProcess.argtypes = [ctypes.c_ulong, ctypes.c_int, ctypes.c_ulong]
        api.OpenProcess.restype = ctypes.c_void_p
        api.GetExitCodeProcess.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_ulong)]
        api.CloseHandle.argtypes = [ctypes.c_void_p]
        observed = []
        original = self.source.host.Job.resume
        def observe(job, process):
            original(job, process)
            until = time.monotonic() + 5
            while not pidfile.exists() and time.monotonic() < until:
                time.sleep(.005)
            self.assertTrue(pidfile.exists(), 'Descendant was not exercised')
            handle = api.OpenProcess(0x1000, False, int(pidfile.read_text()))
            self.assertTrue(handle)
            observed.append(handle)
            gate.write_text('go')
        self.source.host.Job.resume = observe
        self.addCleanup(setattr, self.source.host.Job, 'resume', original)
        self.addCleanup(lambda: [api.CloseHandle(h) for h in observed])
        result = self.trial()
        self.assertEqual(result['failure_reason'], cause)
        self.assertEqual(len(observed), 1)
        exitcode = ctypes.c_ulong()
        self.assertTrue(api.GetExitCodeProcess(observed[0], ctypes.byref(exitcode)))
        self.assertNotEqual(exitcode.value, 259, 'Native descendant is still active')

class NativeIdentityTests(unittest.TestCase):
    def setUp(self):
        self.runner = load()
        self.original_run = subprocess.run
        self.original_command = self.runner.SourceBinding.command
        self.original_git = os.environ['PONTIUS_GIT']
        self.addCleanup(setattr, subprocess, 'run', self.original_run)
        self.addCleanup(os.environ.__setitem__, 'PONTIUS_GIT', self.original_git)

    def disposable(self):
        import shutil
        native = Path(self.original_git).parent.parent / 'mingw64/bin'
        self.assertTrue((native / 'git.exe').is_file(), 'Native Git copy layout unavailable')
        base = Path(tempfile.mkdtemp(prefix='ev-git-'))
        folder = base / 'bin'
        folder.mkdir()
        for path in [native / 'git.exe', native / 'zlib1.dll', *native.glob('lib*.dll')]:
            shutil.copyfile(path, folder / path.name)
        self.git = folder / 'git.exe'
        os.environ['PONTIUS_GIT'] = str(self.git)
        for alias in self.runner.ALIASES:
            sys.modules.pop(alias, None)
        self.drifted, self.changed_launches = False, []
        def record(argv, *args, **kwargs):
            if str(argv[0]) == str(self.git) and self.drifted:
                self.changed_launches.append(list(argv))
            return self.original_run(argv, *args, **kwargs)
        subprocess.run = record

    def drift(self, kind):
        import shutil
        if kind == 'bytes':
            with self.git.open('ab') as stream:
                stream.write(b'finite identity drift\n')
        elif kind == 'file':
            preserved = self.git.with_name('preserved.exe')
            self.git.rename(preserved)
            shutil.copyfile(preserved, self.git)
        else:
            parent = self.git.parent
            preserved = parent.with_name('preserved')
            parent.rename(preserved)
            parent.mkdir()
            for path in preserved.iterdir():
                os.link(path, parent / path.name)
        self.drifted = True

    def test_unchanged_disposable_native_admits_and_rechecks(self):
        self.disposable()
        source = self.runner.admit_source(ROOT)
        source.check()
        self.assertEqual(source.git, self.git)
        self.assertEqual(self.changed_launches, [])

    def test_admitted_native_drift_refuses_before_execution(self):
        for kind in ('bytes', 'file', 'ancestor'):
            with self.subTest(kind=kind):
                self.disposable()
                source = self.runner.admit_source(ROOT)
                self.drift(kind)
                with self.assertRaises((ValueError, OSError)):
                    source.check()
                self.assertEqual(self.changed_launches, [], 'Changed native was executed')

    def test_each_initial_native_command_revalidates_captured_identity(self):
        for boundary in range(1, 7):
            with self.subTest(boundary=boundary):
                self.disposable()
                reached = []
                def inject(source, *args, **kwargs):
                    reached.append(args)
                    if len(reached) == boundary:
                        self.drift('bytes')
                    return self.original_command(source, *args, **kwargs)
                self.runner.SourceBinding.command = inject
                with self.assertRaises((ValueError, OSError)):
                    self.runner.admit_source(ROOT)
                self.assertGreaterEqual(len(reached), boundary, 'Drift boundary not reached')
                self.assertEqual(self.changed_launches, [], 'Changed native was executed')
        self.runner.SourceBinding.command = self.original_command


class RetentionTests(unittest.TestCase):
    def test_completed_trial_retention_fault_clears_score(self):
        self.retention_control(OSError, 'failed', 'trial_failed', 1, 'stdout.bin')

    def test_completed_trial_retention_interrupt_clears_score(self):
        self.retention_control(KeyboardInterrupt, 'interrupted', 'interrupted', 130, 'result.json')

    def retention_control(self, error, state, cause, exit_code, target):
        runner = load()
        for alias in runner.ALIASES:
            sys.modules.pop(alias, None)
        source = runner.admit_source(ROOT)
        base = Path(tempfile.mkdtemp(prefix='ev-retention-'))
        request_path, root = base / 'request.json', base / 'out'
        request_path.write_bytes(runner.encode(dict(version='pontius-v0a-evaluation-request-v1',
            seed='0' * 64, deal_count=1, lineups=[['passive'] * 5], seat_start=0,
            initial_button=0, trial_budget_ms=60000, total_budget_ms=900000)))
        original_trial, original_read = runner.run_trial, runner.read_stable
        completed, fired = [], []
        def real_trial(*args, **kwargs):
            value = original_trial(*args, **kwargs)
            self.assertEqual(value['state'], 'completed', 'Real completed trial not exercised')
            completed.append(value)
            return value
        def fault(path, *args, **kwargs):
            if completed and not fired and path == root / 'u001' / target:
                fired.append(str(path))
                raise error('finite late retention trigger')
            return original_read(path, *args, **kwargs)
        runner.run_trial, runner.read_stable = real_trial, fault
        args = runner.argparse.Namespace(request=request_path, output_root=root,
            evaluation_id='pontius-v0a-evaluation-v1-correctness-retention')
        code = runner.execute(args, source)
        result = json.loads((root / 'result.json').read_bytes())
        unit = json.loads((root / 'u001/result.json').read_bytes())
        row = result['trials'][0]
        self.assertEqual((len(completed), len(fired)), (1, 1))
        self.assertEqual((code, result['status'], row['state']), (exit_code, state, state))
        self.assertEqual((result['failure_reason'], row['failure_reason']), (cause, cause))
        self.assertEqual(unit['state'], 'completed')
        self.assertIs(type(unit['net_chips']), int)
        self.assertTrue(unit['report_complete'] and unit['observation_complete'])
        self.assertTrue((root / 'u001/stdout.bin').read_bytes())
        for key in row.keys() - {'state', 'failure_reason', 'report_complete',
                                 'observation_complete', 'net_chips'}:
            self.assertEqual(row[key], unit[key], key)
        self.assertFalse(row['report_complete'])
        self.assertFalse(row['observation_complete'])
        self.assertIsNone(row['net_chips'])
        self.assertEqual([t['state'] for t in result['trials'][1:]], ['unstarted'] * 11)
        self.assertEqual(result['completed_trials'], 0)
        self.assertIsNone(result['aggregate'])
        self.assertTrue(all(not p['complete'] for p in result['pairs']))
        self.assertEqual([p.name for p in root.glob('u*')], ['u001'])
        self.assertTrue((root / '.publication-pending').is_dir())
        self.assertFalse((root / 'completion.json').exists())
class MatrixTests(unittest.TestCase):
    def test_one_zero_seed_twelve_public_sessions(self):
        runner = load()
        base = Path(tempfile.mkdtemp(prefix='ev-matrix-'))
        request = dict(version='pontius-v0a-evaluation-request-v1', seed='0' * 64,
            deal_count=1, lineups=[['passive'] * 5], seat_start=0, initial_button=0,
            trial_budget_ms=60000, total_budget_ms=900000)
        request_path, root = base / 'request.json', base / 'out'
        request_path.write_bytes(runner.encode(request))
        args = [sys.executable, '-B', '-P', str(TOOL), '--request', str(request_path),
                '--output-root', str(root), '--evaluation-id',
                'pontius-v0a-evaluation-v1-correctness-zero']
        completed = subprocess.run(args, cwd=ROOT, capture_output=True, timeout=950)
        self.assertEqual(completed.returncode, 0, (completed.stdout, completed.stderr, str(root)))
        self.assertTrue(callable(getattr(runner, 'read_completed', None)))
        result = runner.read_completed(root)
        plan = json.loads((root / 'plan.json').read_bytes())
        self.assertEqual((result['planned_trials'], result['completed_trials']), (12, 12))
        self.assertEqual(len(plan['pairs']), 6)
        self.assertEqual([u['strategy'] for u in plan['units']],
                         ['baseline-rules-v1', 'blueprint-v1', 'blueprint-v1',
                          'baseline-rules-v1'] * 3)
        nets, common_deal = {}, None
        for unit in plan['units']:
            unit_root = root / ('u%03d' % unit['ordinal'])
            raw = (root / unit['input_path']).read_bytes()
            data = json.loads(raw)
            self.assertEqual(hashlib.sha256(raw).hexdigest(), unit['input_sha256'])
            self.assertEqual(data['starting_stacks'], [200] * 6)
            self.assertEqual(data['button'], 0)
            self.assertEqual(data['controlled_seat'], unit['pair_index'])
            if common_deal is None:
                common_deal = data['hands']
            self.assertEqual(data['hands'], common_deal)
            report = json.loads((unit_root / 'stdout.bin').read_bytes())
            intent = json.loads((unit_root / 'intent.json').read_bytes())
            launch = json.loads((unit_root / 'launch.json').read_bytes())
            self.assertEqual([launch[k] for k in ('created_suspended', 'assigned', 'resumed')],
                             [True, True, True])
            self.assertEqual(intent['argv'][1:4], ['-B', '-P', 'tools/v0a_table_session.py'])
            self.assertEqual(intent['argv'][4:], ['--session', str(root / unit['input_path']),
                '--blueprint', str(ROOT / 'tests/fixtures/table_host/empty_blueprint.json'),
                '--session-id', unit['session_id'], '--strategy', unit['strategy'],
                '--format', 'json', '--auto'])
            self.assertEqual(set(intent['environment']) - set(runner.KEEP_ENV),
                {'TEMP', 'TMP', 'PONTIUS_GIT', 'PYTHONPATH', 'PYTHONNOUSERSITE',
                 'PYTHONIOENCODING'})
            self.assertEqual(intent['environment']['PYTHONPATH'], str(ROOT / 'src'))
            self.assertEqual(report['hands'][0]['starting_stacks'], [200] * 6)
            stacks = report['hands'][0]['result']['settlement']['final_stacks']
            self.assertEqual(sum(stacks), 1200)
            net = stacks[unit['pair_index']] - 200
            nets[unit['pair_index'], unit['strategy']] = net
            self.assertEqual(result['trials'][unit['ordinal'] - 1]['net_chips'], net)
        baseline = sum(nets[p, 'baseline-rules-v1'] for p in range(6))
        blueprint = sum(nets[p, 'blueprint-v1'] for p in range(6))
        self.assertEqual(result['aggregate']['baseline_net_chips'], baseline)
        self.assertEqual(result['aggregate']['blueprint_net_chips'], blueprint)
        self.assertEqual(result['aggregate']['delta_chips'], baseline - blueprint)
        self.assertEqual(result['aggregate']['mean_delta_denominator'], 6)
        self.assertFalse(result['evidentiary'])
        # Mutants are new retained roots; the consumed correctness root is never edited.
        def rejects(change):
            target = Path(tempfile.mkdtemp(prefix='ev-consumer-'))
            values = {n: json.loads((root / n).read_bytes()) for n in
                      ('request.json', 'plan.json', 'result.json', 'completion.json')}
            change(values)
            values['plan.json']['request_sha256'] = hashlib.sha256(
                runner.encode(values['request.json'])).hexdigest()
            values['result.json']['request_sha256'] = values['plan.json']['request_sha256']
            values['result.json']['plan_sha256'] = hashlib.sha256(
                runner.encode(values['plan.json'])).hexdigest()
            result_raw = runner.encode(values['result.json'])
            values['completion.json'].update(result_sha256=hashlib.sha256(result_raw).hexdigest(),
                                             result_bytes=len(result_raw))
            for name, value in values.items():
                runner.create_file(target / name, runner.encode(value))
            with self.assertRaises((ValueError, KeyError, TypeError)):
                runner.read_completed(target)
        mutations = [
            lambda v: v['result.json']['trials'].pop(),
            lambda v: v['result.json']['trials'][0].update(capture_complete=False),
            lambda v: v['request.json'].update(extra='not admitted'),
            lambda v: v['plan.json']['units'][0].update(session_id='wrong-owner'),
            lambda v: v['plan.json']['pairs'][0].update(rotation=False),
            lambda v: v['result.json']['trials'][0].update(applied_actions_by_kind=None),
            lambda v: v['result.json']['trials'][0].update(
                baseline_fallback_selections={'unrecognized_reason': 1}),
        ]
        for change in mutations:
            with self.subTest(mutation=mutations.index(change)):
                rejects(change)

if __name__ == '__main__':
    unittest.main()
