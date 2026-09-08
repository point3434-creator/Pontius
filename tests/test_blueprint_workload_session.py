"""Real workload ownership and observational-session controls; no performance population."""
from __future__ import annotations

import importlib.util
import contextlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    'workload_session_control', ROOT / 'tools/v0a_blueprint_workload.py')
WORKLOAD = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = WORKLOAD
SPEC.loader.exec_module(WORKLOAD)


class AdmissionControls(unittest.TestCase):
    def test_worker_gate_and_wrong_authority_refuse_before_launch(self):
        # A shaped marker or arbitrary authorization filename cannot grant worker authority.
        if ROOT.drive.upper() == 'D:':
            source = WORKLOAD.FrozenSource(ROOT)
            try:
                source.check()
                self.assertTrue(set(WORKLOAD.ADDITIONS) <= set(source.captured))
                self.assertEqual(source.captured[WORKLOAD.ADDITIONS[0]],
                                 (ROOT / WORKLOAD.ADDITIONS[0]).read_bytes())
                with self.assertRaisesRegex(WORKLOAD.Refusal, 'source_invalid'):
                    WORKLOAD.admit_authority(source, ROOT / 'arbitrary.json', ROOT, None)
            finally:
                source.close()
        else:
            with self.assertRaisesRegex(WORKLOAD.Refusal, 'source_invalid'):
                WORKLOAD.FrozenSource(ROOT)
        claim = dict(version='workload-r002-claim-v1', stage='run',
            nonce_sha256='0' * 64, controller_pid=os.getpid(), source_commit='0' * 40,
            authority_sha256='0' * 64, source_manifest_sha256='0' * 64)
        with self.assertRaisesRegex(WORKLOAD.Refusal, 'source_invalid'):
            WORKLOAD.verify_gate(io.BytesIO(b'x' * 32), claim)
        for change in ({'controller_pid': True}, {'stage': 'resume'}, {'extra': 'value'}):
            with self.subTest(change=change), self.assertRaises(WORKLOAD.Refusal):
                WORKLOAD.verify_gate(io.BytesIO(b'x' * 32), dict(claim, **change))
        with tempfile.TemporaryDirectory() as directory, contextlib.redirect_stderr(io.StringIO()):
            self.assertNotEqual(WORKLOAD.main(['worker', '--source-root', str(ROOT),
                '--run-root', directory, '--authorization', str(Path(directory) / 'arbitrary.json'),
                '--cell', 'not-in-a-plan']), 0)

    def test_owned_file_rejects_replacement_even_with_equal_bytes(self):
        # Content-only validation would miss an object replacement under a held reader.
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'input.json'
            path.write_bytes(b'{"value":1}\n')
            with WORKLOAD.OwnedFile(path, 128) as owned:
                self.assertEqual(owned.raw, b'{"value":1}\n')
                owned.check()
                replacement = path.with_suffix('.replacement')
                replacement.write_bytes(owned.raw)
                try:
                    os.replace(replacement, path)
                except PermissionError:
                    # A real sharing lock that prevents replacement is also ownership.
                    owned.check()
                else:
                    with self.assertRaisesRegex(WORKLOAD.Refusal, 'input_invalid'):
                        owned.check()

    def test_owned_file_rejects_limit_and_late_byte_drift(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'input.json'
            path.write_bytes(b'12345')
            with self.assertRaisesRegex(WORKLOAD.Refusal, 'input_invalid'):
                WORKLOAD.OwnedFile(path, 4)
            with WORKLOAD.OwnedFile(path, 5) as owned:
                path.write_bytes(b'12346')
                with self.assertRaisesRegex(WORKLOAD.Refusal, 'input_invalid'):
                    owned.check()

    def test_create_only_writer_preserves_first_bytes_and_refuses_traversal(self):
        with tempfile.TemporaryDirectory() as directory:
            writer = WORKLOAD.Writer(Path(directory), limit=4)
            reference = writer('case/value.bin', b'abcd')
            self.assertEqual(reference['bytes'], 4)
            with self.assertRaisesRegex(WORKLOAD.Refusal, 'input_invalid'):
                writer('case/value.bin', b'zz')
            self.assertEqual((Path(directory) / 'case/value.bin').read_bytes(), b'abcd')
            for name, raw in (('../escape', b'x'), ('long', b'12345')):
                with self.subTest(name=name), self.assertRaises(WORKLOAD.Refusal):
                    writer(name, raw)

    def test_parser_refuses_arbitrary_program_and_relative_paths_before_execution(self):
        for argv in (['worker', '--cell', 'unknown'],
                     ['read', '--source-root', '.', '--run-root', '.'],
                     ['run', '--source-root', str(ROOT), '--run-root', str(ROOT),
                      '--authorization', str(ROOT / 'missing.json'), '--samples', '1']):
            with self.subTest(argv=argv):
                with contextlib.redirect_stderr(io.StringIO()):
                    self.assertNotEqual(WORKLOAD.main(argv), 0)
        executable, resolved = Path(sys.executable), Path(sys._base_executable)
        config = executable.parents[1] / 'pyvenv.cfg'
        runtime = dict(executable=str(executable), resolved_executable=str(resolved),
            executable_sha256=WORKLOAD.digest(executable.read_bytes()),
            resolved_executable_sha256=WORKLOAD.digest(resolved.read_bytes()))
        record = dict(path=str(config), sha256=WORKLOAD.digest(config.read_bytes()))
        owned = []
        try:
            WORKLOAD.own_runtime(runtime, record, owned)
            self.assertEqual(len(owned), 3)
            with self.assertRaisesRegex(WORKLOAD.Refusal, 'source_invalid'):
                WORKLOAD.own_runtime(runtime, dict(record, sha256='0' * 64), owned)
        finally:
            for item in owned:
                item.close()
        spec = importlib.util.spec_from_file_location('workload_boundary_control',
            ROOT / 'tools/check_stabilization_boundaries.py')
        checker = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = checker
        spec.loader.exec_module(checker)
        sources = {p.relative_to(ROOT).as_posix(): p.read_bytes()
                   for pattern in ('src/pontius/**/*.py', 'tools/**/*.py')
                   for p in ROOT.glob(pattern)}
        checker.enforce_blueprint_workload_import_policy(sources)
        for path, extra in (
            ('tools/v0a_blueprint_workload.py', b'\nimport pontius.no_limit_betting\n'),
            ('tools/v0a_blueprint_workload_report.py', b'\nimport tools.v0a_seeded_deals\n'),
            ('tools/v0a_blueprint_workload_population.py', b'\nimport pontius.river\n'),
            ('tools/v0a_blueprint_workload_measure.py', b'\nimport pontius.v0a.runtime\n'),
            ('src/pontius/immutable_blueprint.py', b'\nimport tools.v0a_blueprint_workload\n'),
            ('tools/v0a_blueprint_workload.py', b'\nexec("pass")\n'),
        ):
            with self.subTest(path=path), self.assertRaises(checker.BoundaryError):
                checker.enforce_blueprint_workload_import_policy(
                    dict(sources, **{path: sources[path] + extra}))


class ProfileControls(unittest.TestCase):
    def test_observer_matches_both_exact_filename_and_qualified_name(self):
        # A same-named function in a foreign file must not be attributed to admission.
        stamps = iter((10, 20))
        observer = WORKLOAD.Observer(ROOT, clock=lambda: next(stamps))
        source = 'class Session:\n def run(self):\n  return 42\n'
        accepted = {}
        exec(compile(source, str(ROOT / 'tools/v0a_table_session.py'), 'exec'), accepted)
        foreign = {}
        exec(compile(source, str(ROOT / 'tools/foreign.py'), 'exec'), foreign)
        sys.setprofile(observer)
        try:
            self.assertEqual(accepted['Session']().run(), 42)
            self.assertEqual(foreign['Session']().run(), 42)
        finally:
            sys.setprofile(None)
        self.assertEqual(observer.events, [
            {'event': 'call', 'point': 'session:Session.run', 'ns': 10},
            {'event': 'return', 'point': 'session:Session.run', 'ns': 20},
        ])


class NativeOwnershipControls(unittest.TestCase):
    def setUp(self):
        self.assertEqual(os.name, 'nt', 'native Windows ownership is a required gate')

    def invoke(self, script, **options):
        return WORKLOAD.supervise(
            [sys.executable, '-B', '-P', '-c', script], ROOT,
            os.environ.copy(), timeout_ns=5_000_000_000, **options)

    def test_native_worker_exit_and_captures_are_observed(self):
        result = self.invoke("import sys; print('owned'); sys.stderr.write('err')")
        self.assertEqual((result['exit_code'], result['stdout'], result['stderr']),
                         (0, b'owned\r\n', b'err'))
        self.assertEqual(result['cleanup'], {'verified': True, 'active': 0})
        self.assertIsNone(result['cause'])
        self.assertGreater(result['outer_ns'], 0)

    def test_timeout_terminates_real_descendant_and_does_not_report_clean_success(self):
        script = ("import subprocess,sys,time; p=subprocess.Popen([sys.executable,'-c',"
                  "'import time; time.sleep(60)']); print(p.pid,flush=True); time.sleep(60)")
        result = self.invoke(script, stop=lambda elapsed, samples: (
            'budget_exhausted' if elapsed >= 500_000_000 else None))
        self.assertEqual(result['cause'], 'budget_exhausted')
        self.assertEqual(result['cleanup'], {'verified': True, 'active': 0})
        child_pid = int(result['stdout'].strip())
        self.assertFalse(WORKLOAD.process_alive(child_pid))

    def test_output_overflow_retains_bounded_prefix_and_closes_owned_job(self):
        result = self.invoke("import os,time; os.write(1,b'x'*20000); time.sleep(60)",
                             stdout_limit=1024)
        self.assertEqual(result['cause'], 'capture_limit')
        self.assertEqual(result['stdout'], b'x' * 1024)
        self.assertIs(result['truncated'], True)
        self.assertEqual(result['cleanup'], {'verified': True, 'active': 0})

    def test_controlled_resource_and_interrupt_triggers_use_real_native_cleanup(self):
        for cause in ('resource_limit', 'interrupted'):
            with self.subTest(cause=cause):
                result = self.invoke('import time; time.sleep(60)',
                    stop=lambda elapsed, samples: cause if elapsed > 100_000_000 else None)
                self.assertEqual(result['cause'], cause)
                self.assertEqual(result['cleanup'], {'verified': True, 'active': 0})
                self.assertFalse(WORKLOAD.process_alive(result['redirector_pid']))
        # A stop caused by the final sample must precede the acknowledgement that
        # releases retained owners. Only the threshold trigger is controlled.
        script = ("import json,os; print(json.dumps({'pid':os.getpid(),'stage':'final'}),"
                  "flush=True); assert os.read(0,1)==b'G'; print('ACK',flush=True)")
        result = self.invoke(script, worker=True, stop=lambda elapsed, samples:
            'resource_limit' if any(s['stage'] == 'final' for s in samples) else None)
        self.assertEqual(result['cause'], 'resource_limit')
        self.assertNotIn(b'ACK', result['stdout'])
        self.assertEqual(result['cleanup'], {'verified': True, 'active': 0})

    def test_orphaned_descendant_is_failure_even_when_redirector_exits_zero(self):
        # A descendant still finishing at root exit is allowed to close inside verification;
        # a surviving sleeper must be terminated and cannot become successful ownership.
        finishing = self.invoke("import subprocess,sys; subprocess.Popen([sys.executable,'-c',"
                                "'import time; time.sleep(0.08)'])")
        self.assertIsNone(finishing['cause'])
        self.assertEqual(finishing['cleanup'], {'verified': True, 'active': 0})
        result = self.invoke("import subprocess,sys; subprocess.Popen([sys.executable,'-c',"
                             "'import time; time.sleep(60)'])")
        self.assertEqual(result['cause'], 'worker_failed')
        self.assertEqual(result['cleanup'], {'verified': True, 'active': 0})

    def test_sampler_uses_actual_interpreter_pid_and_waits_for_final_sample(self):
        script = ("import json,os,sys; print(json.dumps({'pid':os.getpid(),'stage':'ready'}),"
                  "flush=True); assert os.read(0,1)==b'G'; keep=bytearray(1000000); "
                  "print(json.dumps({'pid':os.getpid(),'stage':'final'}),flush=True); "
                  "assert os.read(0,1)==b'G'")
        result = self.invoke(script, worker=True)
        self.assertIsNone(result['cause'], result)
        stages = [s for s in result['samples'] if s['stage'] != 'periodic']
        self.assertEqual([s['stage'] for s in stages], ['ready', 'final'])
        self.assertTrue(all(s['private_commit'] > 0 and s['working_set'] > 0 for s in stages))
        self.assertEqual(len({s['pid'] for s in stages}), 1)
        self.assertNotEqual(stages[0]['pid'], result['redirector_pid'])
        self.assertFalse(WORKLOAD.process_alive(stages[0]['pid']))


class LiveSessionControls(unittest.TestCase):
    def test_real_control_sessions_preserve_reference_actions_and_original_ledger(self):
        # Exactly one finite invocation: 8 stock and 8 diagnostic sessions; no retries.
        self.assertEqual(ROOT.drive.upper(), 'D:', 'real sessions require a fresh D-local snapshot')
        host = WORKLOAD.load_tool('host', ROOT)
        source = host.Source(ROOT)
        validator = host, source, source.load()
        population = WORKLOAD.load_tool('population', ROOT)
        reader = WORKLOAD.load_tool('report', ROOT)
        control = json.loads((ROOT / 'tests/fixtures/blueprint_workload/control.json').read_bytes())
        output = Path(tempfile.mkdtemp(prefix='workload-session-controls-'))
        transcripts = {}
        for seat in (0, 3):
            for strategy in ('blueprint-v1', 'baseline-rules-v1'):
                factor = population.factors(
                    'query', seat * 12 + int(strategy == 'baseline-rules-v1'))
                transcripts[seat, strategy] = population.trajectory(factor, seed=control['seed'])
        member = transcripts[3, 'blueprint-v1']['contexts'][0]
        for size, members in ((0, []), (1, [member])):
            (output / f'artifact-{size}.json').write_bytes(population.artifact(members)[0])
        for seat in (0, 3):
            (output / f'session-{seat}.json').write_bytes(WORKLOAD.encode(dict(
                version='pontius-v0a-table-session-v1', button=0, controlled_seat=seat,
                starting_stacks=[200] * 6, small_blind=1, big_blind=2,
                opponents=[None if s == seat else 'passive' for s in range(6)],
                hands=[control['deal']])))
        launched = 0
        for size in (0, 1):
            for seat in (0, 3):
                for strategy in ('blueprint-v1', 'baseline-rules-v1'):
                    paired = []
                    for instrumented in (False, True):
                        ordinal = launched
                        baseline = strategy == 'baseline-rules-v1'
                        prefix = 'pontius-v0a-table-session-v2-correctness-' if baseline else (
                            'pontius-v0a-table-session-v1-correctness-')
                        params = dict(diagnostic=instrumented, ordinal=ordinal, deal=0, seat=seat,
                            lineup=0, strategy=strategy,
                            session_id=prefix + f'workload-control-{ordinal}',
                            session_path=str(output / f'session-{seat}.json'),
                            blueprint_path=str(output / f'artifact-{size}.json'))
                        cell = dict(id=f'control-{ordinal}', runtime='control', kind='session',
                                    size=size, parameters=params)
                        arguments = ['--session', params['session_path'], '--blueprint',
                            params['blueprint_path'], '--session-id', params['session_id'],
                            '--strategy', strategy, '--auto', '--format', 'json']
                        profile = output / f'profile-{ordinal}.json'
                        if instrumented:
                            bootstrap = ('import importlib.util,sys; from pathlib import Path; '
                                "s=importlib.util.spec_from_file_location('workload_diagnostic',"
                                "Path.cwd()/'tools/v0a_blueprint_workload.py'); "
                                'm=importlib.util.module_from_spec(s); sys.modules[s.name]=m; '
                                's.loader.exec_module(m); '
                                'raise SystemExit(m.diagnostic(Path.cwd(),sys.argv[2:],'
                                'Path(sys.argv[1])))')
                            argv = [sys.executable, '-B', '-P', '-c', bootstrap,
                                    str(profile), *arguments]
                        else:
                            argv = [sys.executable, '-B', '-P',
                                    str(ROOT / WORKLOAD.TOOLS['session'][0]),
                                    *arguments]
                        (output / f'intent-{ordinal}.json').write_bytes(
                            WORKLOAD.encode(dict(argv=argv)))
                        launched += 1
                        result = WORKLOAD.supervise(argv, ROOT, os.environ.copy(),
                                                     timeout_ns=150_000_000_000)
                        for channel in ('stdout', 'stderr'):
                            (output / f'{ordinal}-{channel}.bin').write_bytes(result[channel])
                        self.assertIsNone(result['cause'], result)
                        self.assertEqual(result['cleanup'], {'verified': True, 'active': 0})
                        events = []
                        if instrumented:
                            events = [dict(row, ns=row['ns'] - result['launch_ns'])
                                      for row in reader.parse_json(profile.read_bytes())]
                            phases = reader.reduce_spans(events, result['outer_ns'])
                            self.assertTrue(phases)
                        observation = WORKLOAD.session_observations(result['stdout'], cell,
                            transcripts[seat, strategy], ROOT, reader, events, validator)
                        raw_report = reader.parse_json(result['stdout'])
                        child = raw_report['hands'][0]['result']
                        captured = __import__('base64').b64decode(child['child_stdout_base64'])
                        frames = [reader.parse_json(row) for row in captured.splitlines()]
                        original = [row['decision'] for row in frames
                                    if row['type'] == 'event_result'
                                    and row['decision'] is not None]
                        self.assertEqual([a['elapsed_ns'] for a in observation['actions']],
                                         [a['timing']['elapsed_ns'] for a in original])
                        self.assertEqual(observation['actions'][0]['first'], True)
                        self.assertEqual(observation['actions'][0]['event_index'],
                                         original[0]['event_index'])
                        if size == 0:
                            self.assertTrue(all(a['hit'] is False for a in observation['actions']))
                        elif seat == 3:
                            self.assertIs(observation['actions'][0]['hit'], True)
                        paired.append(observation['settlement'])
                    self.assertEqual(paired[0], paired[1])
        self.assertEqual(launched, 16)
        (output / 'completed.json').write_bytes(WORKLOAD.encode(dict(launched=launched,
            standing='finite correctness only', versions=sys.version)))


if __name__ == '__main__':
    unittest.main()
