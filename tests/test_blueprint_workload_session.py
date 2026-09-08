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
import types
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
        self.counterfeit_worker_control()

    def counterfeit_worker_control(self):
        # All r001 self-reported hashes/identities and the nonce agree. Only
        # accepted invocation authority and actual controller ownership are absent.
        git = Path(os.environ['PONTIUS_GIT'])
        def inspected(*args):
            result = subprocess.run([str(git), '--no-replace-objects', '--no-optional-locks',
                '-C', str(ROOT), *args], capture_output=True, check=True, timeout=30)
            return result.stdout
        names = inspected('ls-tree', '-r', '--name-only', '-z', 'HEAD').split(b'\0')
        captured = {name.decode('utf-8'): (ROOT / name.decode('utf-8')).read_bytes()
                    for name in names if name}
        source = types.SimpleNamespace(
            commit=inspected('rev-parse', 'HEAD').decode('ascii').strip(),
            manifest=WORKLOAD.FrozenSource.raw_manifest(captured))
        stage_sample, stdin = WORKLOAD.stage_sample, sys.stdin
        reached = []

        class PayloadReached(Exception):
            pass

        def no_payload(stage):
            reached.append(stage)
            raise PayloadReached('counterfeit authority reached population dispatch')

        try:
            with tempfile.TemporaryDirectory() as directory:
                run_root = Path(directory)
                (run_root / 'admission').mkdir()
                authority = ROOT / WORKLOAD.AUTHORITY
                self.assertFalse(authority.exists(), 'this control needs unaccepted authority')
                authority.write_bytes(WORKLOAD.encode({'run_root': str(run_root)}))
                nonce = b'x' * 32
                claim = dict(version='workload-r002-claim-v1', stage='qualify',
                    nonce_sha256=WORKLOAD.digest(nonce), controller_pid=os.getpid(),
                    source_commit=source.commit,
                    authority_sha256=WORKLOAD.digest(authority.read_bytes()),
                    source_manifest_sha256=WORKLOAD.digest(source.manifest))
                (run_root / 'qualify-claim.json').write_bytes(WORKLOAD.encode(claim))
                runtime = dict(id='3.11', version='.'.join(map(str, sys.version_info[:3])),
                    source_root=str(ROOT), executable=sys.executable,
                    resolved_executable=sys._base_executable,
                    source_sha256=WORKLOAD.digest(source.manifest))
                (run_root / 'runtimes.json').write_bytes(WORKLOAD.encode([runtime]))
                (run_root / 'admission/3.11-source.manifest').write_bytes(source.manifest)
                sys.stdin = types.SimpleNamespace(buffer=io.BytesIO(nonce))
                WORKLOAD.stage_sample = no_payload
                try:
                    try:
                        with contextlib.redirect_stderr(io.StringIO()):
                            WORKLOAD.main(['worker', '--source-root', str(ROOT),
                                '--run-root', str(run_root), '--authorization', str(authority),
                                '--cell', 'qualification'])
                    except PayloadReached:
                        pass
                    self.assertEqual(reached, [],
                        'self-consistent caller files granted an unaccepted workload invocation')
                finally:
                    authority.unlink()  # Only this control's new untracked counterfeit file.
        finally:
            WORKLOAD.stage_sample, sys.stdin = stage_sample, stdin

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
        self.interrupted_publication_control()
        self.terminal_retention_control()

    def interrupted_publication_control(self):
        # An actual flushed staging write is interrupted before publication. The
        # canonical result must remain absent, with its attempted bytes retained.
        fsync = WORKLOAD.os.fsync
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            writer = WORKLOAD.Writer(root)
            def interrupted(fd):
                fsync(fd)
                raise KeyboardInterrupt('controlled publication interruption')
            WORKLOAD.os.fsync = interrupted
            try:
                with self.assertRaises(KeyboardInterrupt):
                    writer('cell/result.json', b'{"original":true}\n')
            finally:
                WORKLOAD.os.fsync = fsync
            self.assertFalse((root / 'cell/result.json').exists(),
                             'an interrupted write exposed a canonical result')
            attempted = [path.read_bytes() for path in root.rglob('*') if path.is_file()]
            self.assertIn(b'{"original":true}\n', attempted)
            writer('cell/result.json', b'{"original":true}\n')
            self.assertEqual((root / 'cell/result.json').read_bytes(), b'{"original":true}\n')

    def allocation_retention_control(self):
        self.terminal_retention_control(('allocate-1',))

    def terminal_retention_control(self, phases=None):
        # This is a finite controller-finalization unit, not invocation admission:
        # literal accepted slots and an injected admission refusal prevent ALL
        # worker launches. Real Writer and closed result/terminal readers remain.
        reader = WORKLOAD.load_tool('report', ROOT)
        writer_type, loader = WORKLOAD.Writer, WORKLOAD.load_tool
        claim, admit, supervise = (WORKLOAD.claim_stage, WORKLOAD.admit_run_runtimes,
                                   WORKLOAD.supervise)
        environment = WORKLOAD.runtime_environment
        phases = phases or ('allocate-1', 'intent-0', 'intent-1', 'intent-2', 'result-0',
                            'result-1-after', 'validate-1', 'terminal')
        for phase in phases:
            with self.subTest(retention_phase=phase), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                population = {'literal_controller_control': True}
                runtime = dict(id='3.11', version='3.11.15', executable=sys.executable,
                    executable_sha256='0' * 64, resolved_executable=sys._base_executable,
                    resolved_executable_sha256='0' * 64, source_root=str(ROOT),
                    run_root=str(root), source_sha256='0' * 64, protocol_sha256='0' * 64,
                    authorization=str(ROOT / WORKLOAD.AUTHORITY))
                cells = [dict(id=f'control-{i}', runtime='3.11', kind='construction', size=0,
                    parameters={'observation': i}, argv=[sys.executable]) for i in range(3)]
                plan = dict(version='workload-r002-plan-v1', runtimes=[runtime], cells=cells,
                    population_sha256=WORKLOAD.digest(WORKLOAD.encode(population)))
                source = types.SimpleNamespace(root=ROOT, commit='0' * 40,
                    captured={WORKLOAD.AUTHORITY: b'{}\n'}, check=lambda: None)
                writer = writer_type(root)
                for name, value in (('plan.json', plan), ('population.json', population)):
                    writer(name, WORKLOAD.encode(value))
                manifest = writer('qualification-manifest.json', WORKLOAD.encode(
                    dict(files=list(writer.references))))
                writer('qualified.json', WORKLOAD.encode(dict(source_commit=source.commit,
                    plan_sha256=WORKLOAD.digest(WORKLOAD.encode(plan)), manifest=manifest)))
                fired, committed = [], {}

                class FaultWriter(writer_type):
                    def __call__(self, name, raw):
                        targets = {f'intent-{i}': f'cells/control-{i}/intent.json'
                                   for i in range(3)}
                        targets.update({'result-0': 'cells/control-0/result.json',
                            'result-1-after': 'cells/control-1/result.json',
                            'terminal': 'terminal.json'})
                        selected = not fired and targets.get(phase) == name
                        if selected and phase != 'result-1-after':
                            fired.append(name)
                            raise KeyboardInterrupt('one retained publication fault')
                        result = super().__call__(name, raw)
                        if name.endswith('/result.json'):
                            committed[name] = raw
                        if selected:
                            fired.append(name)
                            raise KeyboardInterrupt('after canonical result installation')
                        return result

                validate = reader.validate_result
                environment_calls = []
                def checked_environment(*args):
                    environment_calls.append(args)
                    if phase == 'allocate-1' and not fired and len(environment_calls) == 2:
                        fired.append('allocation')
                        raise KeyboardInterrupt('one census-allocation interruption')
                    return environment(*args)
                def checked_result(record):
                    if phase == 'validate-1' and not fired and record['cell_id'] == 'control-1':
                        fired.append('validate')
                        raise KeyboardInterrupt('one retained result-validation fault')
                    return validate(record)
                def refused(*args):
                    raise WORKLOAD.Refusal('coverage_missing')
                def no_launch(*args, **kwargs):
                    raise AssertionError('retention control attempted a workload launch')
                inert_source = types.SimpleNamespace(load=lambda: None)
                modules = {'host': types.SimpleNamespace(Source=lambda root: inert_source),
                    'population': types.SimpleNamespace(freeze_plan=lambda *unused: plan)}
                WORKLOAD.Writer = FaultWriter
                WORKLOAD.load_tool = lambda name, *args: modules[name]
                WORKLOAD.claim_stage, WORKLOAD.admit_run_runtimes = lambda *args: b'', refused
                WORKLOAD.supervise, reader.validate_result = no_launch, checked_result
                WORKLOAD.runtime_environment = checked_environment
                try:
                    code = WORKLOAD.run(types.SimpleNamespace(run_root=root), source,
                                        reader, [source], {})
                    self.assertNotEqual(code, 0)
                    self.assertEqual(len(fired), 1)
                    self.assertTrue((root / 'terminal.json').is_file(),
                                    'a recoverable retention fault lost the planned census')
                    terminal = reader.parse_json((root / 'terminal.json').read_bytes())
                    self.assertEqual([row['cell_id'] for row in terminal['cells']],
                                     [cell['id'] for cell in cells])
                    for cell, row in zip(cells, terminal['cells'], strict=True):
                        prefix = f'cells/{cell["id"]}/'
                        result = reader.parse_json((root / (prefix + 'result.json')).read_bytes())
                        validate(result)
                        self.assertEqual(result['status'], row['status'])
                        self.assertNotEqual(result['status'], 'completed')
                        if phase in ('validate-1', 'result-1-after') and cell['id'] == 'control-1':
                            self.assertEqual(result['status'], 'unattempted')
                        self.assertIsNone(result['outer_ns'])
                        self.assertTrue((root / (prefix + 'intent.json')).is_file())
                        self.assertTrue((root / (prefix + 'environment.json')).is_file())
                    for name, raw in committed.items():
                        self.assertEqual((root / name).read_bytes(), raw)
                finally:
                    WORKLOAD.Writer, WORKLOAD.load_tool = writer_type, loader
                    WORKLOAD.claim_stage, WORKLOAD.admit_run_runtimes = claim, admit
                    WORKLOAD.supervise, reader.validate_result = supervise, validate
                    WORKLOAD.runtime_environment = environment

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
        # Hold the real process object through the independent exit observation.
        # A PID can be reused after the supervisor releases its final handle.
        created, popen = [], WORKLOAD.subprocess.Popen

        def observed_popen(*args, **kwargs):
            process = popen(*args, **kwargs)
            created.append(process)
            return process

        WORKLOAD.subprocess.Popen = observed_popen
        try:
            result = WORKLOAD.supervise(
                [sys.executable, '-B', '-P', '-c', script], ROOT,
                os.environ.copy(), timeout_ns=5_000_000_000, **options)
            self.assertEqual(len(created), 1)
            result['held_root_signalled'] = WORKLOAD.process_api().WaitForSingleObject(
                int(created[0]._handle), 0) == 0
            result['held_root_alive'] = WORKLOAD.process_alive(created[0].pid)
            return result
        finally:
            WORKLOAD.subprocess.Popen = popen

    def test_native_worker_exit_and_captures_are_observed(self):
        result = self.invoke("import sys; print('owned'); sys.stderr.write('err')")
        self.assertEqual((result['exit_code'], result['stdout'], result['stderr']),
                         (0, b'owned\r\n', b'err'))
        self.assertEqual(result['cleanup'], {'verified': True, 'active': 0})
        self.assertIsNone(result['cause'])
        self.assertGreater(result['outer_ns'], 0)
        self.assignment_failure_control()
        self.native_worker_grant_control()

    def assignment_failure_control(self):
        # The real AssignProcessToJobObject call fails on an invalid job handle.
        # Creation, suspended state, rollback, and exit observations remain native.
        loader = WORKLOAD.load_tool
        host = loader('host', ROOT)
        assign, processes = host.Job.assign, []

        def fail_assignment(job, process):
            processes.append(process)
            native = job.api.AssignProcessToJobObject
            job.api.AssignProcessToJobObject = lambda handle, child: native(None, child)
            try:
                assign(job, process)
            finally:
                job.api.AssignProcessToJobObject = native

        host.Job.assign = fail_assignment
        WORKLOAD.load_tool = lambda name, *args, **kwargs: (
            host if name == 'host' else loader(name, *args, **kwargs))
        try:
            result = self.invoke('import time; time.sleep(60)')
            self.assertEqual(result['cause'], 'containment_failed')
            self.assertEqual(len(processes), 1)
            self.assertFalse(WORKLOAD.process_alive(processes[0].pid),
                             'a failed assignment left the real suspended root alive')
            self.assertIsNotNone(processes[0].poll(), 'created process was not reaped')
            self.assertEqual(result['cleanup'], {'verified': True, 'active': 0})
        finally:
            WORKLOAD.load_tool = loader
            # RED must not leak the suspended process it detects.
            for process in processes:
                if process.poll() is None:
                    process.kill()
                process.wait(timeout=5)

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

    def typed_worker_failure_control(self):
        # Actual child stderr and exit travel through the native supervisor. A
        # typed payload refusal must survive transport and later cleanup facts.
        for cause in ('coverage_missing', 'parity_failed', 'input_invalid', 'interrupted'):
            with self.subTest(worker_cause=cause):
                failure = dict(version='workload-r002-worker-failure-v1', cell_id='control',
                    cause=cause, secondary=['cleanup_failed'], exception_type='Refusal')
                raw = b'PONTIUS_WORKLOAD_CONTROL ' + WORKLOAD.encode(failure)
                script = f'import os; os.write(2, {raw!r}); raise SystemExit(1)'
                result = self.invoke(script, worker=True)
                self.assertEqual(result['cause'], cause,
                                 'the original typed worker refusal was erased')
                self.assertEqual(result['worker_failure'], failure)
                self.assertEqual(result['secondary'], ['cleanup_failed'])
                self.assertEqual(result['exit_code'], 1)
                self.assertIs(result['held_root_signalled'], True)
                self.assertEqual(result['stderr'], raw)

    def test_controlled_resource_and_interrupt_triggers_use_real_native_cleanup(self):
        self.native_secondary_failure_control()
        self.typed_worker_failure_control()
        for cause in ('resource_limit', 'interrupted'):
            with self.subTest(cause=cause):
                result = self.invoke('import time; time.sleep(60)',
                    stop=lambda elapsed, samples: cause if elapsed > 100_000_000 else None)
                self.assertEqual(result['cause'], cause)
                self.assertEqual(result['cleanup'], {'verified': True, 'active': 0})
                self.assertTrue(result['held_root_signalled'], result)
                self.assertFalse(result['held_root_alive'], result)
        # A stop caused by the final sample must precede the acknowledgement that
        # releases retained owners. Only the threshold trigger is controlled.
        script = ("import json,os; print(json.dumps({'pid':os.getpid(),'stage':'final'}),"
                  "flush=True); assert os.read(0,1)==b'G'; print('ACK',flush=True)")
        result = self.invoke(script, worker=True, stop=lambda elapsed, samples:
            'resource_limit' if any(s['stage'] == 'final' for s in samples) else None)
        self.assertEqual(result['cause'], 'resource_limit')
        self.assertNotIn(b'ACK', result['stdout'])
        self.assertEqual(result['cleanup'], {'verified': True, 'active': 0})

    def native_secondary_failure_control(self):
        # Close the real thread handle at the controlled resume trigger. The
        # unchanged Job then observes both a native resume-path failure and an
        # actual invalid-handle failure while closing that same owned handle.
        loader = WORKLOAD.load_tool
        host = loader('host', ROOT)
        resume, observed = host.Job.resume, []

        def fail_resume(job, process):
            open_thread, close = job.api.OpenThread, job.api.CloseHandle

            def closed_thread(*args):
                handle = open_thread(*args)
                self.assertTrue(handle)
                self.assertTrue(close(handle))
                observed.append('trigger_closed_thread')
                return handle

            def observe_close(handle):
                value = close(handle)
                if not value:
                    observed.append('native_close_failed')
                return value

            job.api.OpenThread, job.api.CloseHandle = closed_thread, observe_close
            try:
                resume(job, process)
            finally:
                job.api.OpenThread, job.api.CloseHandle = open_thread, close

        host.Job.resume = fail_resume
        WORKLOAD.load_tool = lambda name, *args, **kwargs: (
            host if name == 'host' else loader(name, *args, **kwargs))
        try:
            result = self.invoke('import time; time.sleep(60)')
            self.assertEqual(observed, ['trigger_closed_thread', 'native_close_failed'])
            self.assertEqual(result['cause'], 'containment_failed')
            self.assertIn('cleanup_failed', result['secondary'],
                          'the originating native secondary failure disappeared')
            self.assertFalse(WORKLOAD.process_alive(result['redirector_pid']))
        finally:
            WORKLOAD.load_tool = loader

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

    def native_worker_grant_control(self):
        """Eleven native capability controls; literal bindings never authorize a workload."""
        self.assertEqual(ROOT.drive.upper(), 'D:', 'native payloads require the D snapshot')
        child = r'''
import importlib.util, json, os, sys
from pathlib import Path
source, retained, mode = sys.argv[1:4]
spec = importlib.util.spec_from_file_location('native_grant_child',
    Path(source) / 'tools/v0a_blueprint_workload.py')
w = importlib.util.module_from_spec(spec)
spec.loader.exec_module(w)
root = Path(retained)
claim = json.loads((root / 'run-claim.json').read_bytes())
intent = json.loads((root / 'cells' / mode / 'worker-grant-intent.json').read_bytes())
if mode == 'wrong-owner':
    owner = w.ProcessIdentity(os.getpid())
    try:
        claim['controller_pid'] = owner.pid
        claim['controller_created_100ns'] = owner.created
    finally:
        owner.close()
elif mode == 'wrong-creation':
    claim['controller_created_100ns'] += 1
elif mode == 'bad-nonce':
    intent['nonce_sha256'] = '0' * 64
elif mode == 'wrong-cell':
    intent['cell_id'] = 'different-cell'
lease = []
try:
    lease.extend(w.verify_gate(sys.stdin.buffer, claim, intent=intent,
        receipt_path=root / 'cells' / mode / 'worker-grant.json'))
    if mode == 'duplicate-ready':
        me = w.ProcessIdentity(os.getpid())
        try:
            ready = dict(version=w.VERSION + '-worker-ready-v1', cell_id=mode,
                intent_sha256=w.digest(w.encode(intent)), worker_pid=me.pid,
                worker_created_100ns=me.created,
                pipe_server_pid=claim['controller_pid'],
                pipe_client_pid=claim['controller_pid'])
        finally:
            me.close()
        sys.stderr.buffer.write(w.GRANT_PREFIX + w.encode(ready))
        sys.stderr.buffer.flush()
    w.stage_sample('ready')
    # Every case has a marker, so an unintended release cannot hide in a refusal case.
    (root / (mode + '-marker.json')).write_bytes(w.encode({'released': True}))
    w.stage_sample('final')
finally:
    for owned in reversed(lease):
        owned.close()
'''
        held_exits = []
        original_close = WORKLOAD.ProcessIdentity.close

        def observed_close(identity):
            # Observe the same held object immediately before its real CloseHandle.
            # A post-close PID lookup would permit both PID reuse and termination races.
            try:
                if identity.handle and identity.pid != os.getpid():
                    row = dict(pid=identity.pid,
                        created_100ns=WORKLOAD.process_created(identity.handle),
                        wait=identity.api.WaitForSingleObject(identity.handle, 0))
                    held_exits.append(row)
                    self.assertEqual(row['created_100ns'], identity.created, row)
                    self.assertEqual(row['wait'], 0, row)
            finally:
                original_close(identity)

        class Check:
            def __init__(self, fail=False):
                self.count, self.fail = 0, fail

            def check(self):
                self.count += 1
                if self.fail:
                    raise WORKLOAD.Refusal('source_invalid')

        def invoke(control_root, name, gate, *, outcome=None, launches=1):
            # Hold Popen's exact root process object until the independent native wait.
            created, popen = [], WORKLOAD.subprocess.Popen

            def observed_popen(*args, **kwargs):
                process = popen(*args, **kwargs)
                created.append(process)
                return process

            WORKLOAD.subprocess.Popen = observed_popen
            try:
                result = WORKLOAD.supervise([sys.executable, '-B', '-P',
                    str(control_root / 'child-control.py'), str(ROOT), str(control_root), name],
                    ROOT, os.environ.copy(), timeout_ns=15_000_000_000,
                    worker=True, gate=gate, outcome=outcome)
                self.assertEqual(len(created), launches, result)
                for process in created:
                    self.assertEqual(WORKLOAD.process_api().WaitForSingleObject(
                        int(process._handle), 0), 0, result)
                    self.assertIsNotNone(process.poll(), result)
                self.assertEqual(result['cleanup'], {'verified': True, 'active': 0}, result)
                self.assertIn('worker_grant', result)
                grant = result['worker_grant']
                if grant is not None:
                    expected = dict(pid=grant['worker_pid'],
                        created_100ns=grant['worker_created_100ns'], wait=0)
                    self.assertIn(expected, held_exits, result)
                return result
            finally:
                WORKLOAD.subprocess.Popen = popen
                # A regressed supervisor must not leave its real owned root running.
                for process in created:
                    if WORKLOAD.process_api().WaitForSingleObject(int(process._handle), 0) != 0:
                        process.kill()
                    self.assertEqual(WORKLOAD.process_api().WaitForSingleObject(
                        int(process._handle), 10000), 0)
                    process.wait(timeout=0)

        WORKLOAD.ProcessIdentity.close = observed_close
        try:
            with tempfile.TemporaryDirectory() as directory:
                control_root = Path(directory)
                (control_root / 'child-control.py').write_text(
                    child, encoding='utf-8', newline='\n')
                source = types.SimpleNamespace(root=ROOT, commit='0' * 40, tree='1' * 40,
                    manifest=b'finite native helper control\n',
                    captured={WORKLOAD.AUTHORITY: b'literal authority\n'})
                runtime = dict(id='.'.join(map(str, sys.version_info[:2])), source_root=str(ROOT),
                               source_sha256=WORKLOAD.digest(source.manifest))
                writer = WORKLOAD.Writer(control_root)
                claim = WORKLOAD.claim_stage(control_root, writer, 'run', source,
                                             source.captured[WORKLOAD.AUTHORITY])
                names = ('positive', 'wrong-owner', 'wrong-creation', 'bad-nonce', 'wrong-cell',
                         'duplicate-ready', 'check-failure', 'publication-failure',
                         'published-interrupt')
                for name in names:
                    with self.subTest(native_grant=name):
                        check = Check(name == 'check-failure')
                        cell = dict(id=name, runtime=runtime['id'], kind='literal-native-control')
                        gate = WORKLOAD.prepare_worker_grant(claim, source, runtime, cell, writer,
                            plan_raw=b'literal plan\n', checks=(check,))
                        if name == 'publication-failure':
                            def refused_publication(relative, raw):
                                raise WORKLOAD.Refusal('input_invalid')
                            gate['writer'] = refused_publication
                        elif name == 'published-interrupt':
                            def published_interrupt(relative, raw):
                                writer(relative, raw)
                                raise KeyboardInterrupt('after immutable grant publication')
                            gate['writer'] = published_interrupt
                        outcome = {'stale': 'must be replaced'}
                        result = invoke(control_root, name, gate, outcome=outcome)
                        self.assertEqual(outcome, result)
                        self.assertNotIn('stale', outcome)
                        marker = control_root / (name + '-marker.json')
                        if name == 'positive':
                            self.assertIsNone(result['cause'], result)
                            self.assertEqual(result['secondary'], [], result)
                            self.assertEqual(marker.read_bytes(),
                                             WORKLOAD.encode({'released': True}))
                            grant = result['worker_grant']
                            self.assertIs(grant['consumed'], True)
                            self.assertIs(grant['job_member'], True)
                            self.assertEqual(grant['controller_pid'], os.getpid())
                            self.assertEqual(grant['pipe_server_pid'], os.getpid())
                            self.assertEqual(grant['pipe_client_pid'], os.getpid())
                            self.assertEqual(grant['redirector_pid'], result['redirector_pid'])
                            self.assertEqual(grant['worker_pid'], result['samples'][0]['pid'])
                            self.assertNotEqual(grant['worker_pid'], os.getpid())
                            self.assertEqual(check.count, 1)
                            with self.subTest(native_grant='used-grant-replay'):
                                replay = invoke(control_root, name, gate, launches=0)
                                self.assertEqual(replay['cause'], 'source_invalid')
                                self.assertIsNone(replay['redirector_pid'])
                            with self.subTest(native_grant='intent-recreation'):
                                with self.assertRaises(WORKLOAD.Refusal):
                                    WORKLOAD.prepare_worker_grant(claim, source, runtime, cell,
                                        writer, plan_raw=b'literal plan\n', checks=(Check(),))
                        else:
                            self.assertIsNotNone(result['cause'], result)
                            self.assertEqual(result['samples'], [], result)
                            self.assertFalse(marker.exists(), result)
                            if name in ('check-failure', 'publication-failure', 'wrong-cell',
                                        'duplicate-ready'):
                                expected = ('input_invalid' if name == 'publication-failure'
                                            else 'source_invalid')
                                self.assertEqual(result['cause'], expected, result)
                            if name == 'publication-failure':
                                self.assertIs(gate['used'], True)
                                self.assertIsNone(result['worker_grant'])
                            elif name == 'published-interrupt':
                                self.assertIs(gate['used'], True)
                                self.assertEqual(result['cause'], 'interrupted')
                                receipt = control_root / 'cells' / name / 'worker-grant.json'
                                self.assertEqual(result['worker_grant'],
                                                 json.loads(receipt.read_bytes()))
                            elif name == 'check-failure':
                                self.assertEqual(check.count, 1)
                                self.assertIs(gate['used'], False)
                        grant = result['worker_grant']
                        if grant is not None:
                            ready = {key: grant[key] for key in ('cell_id', 'intent_sha256',
                                'worker_pid', 'worker_created_100ns', 'pipe_server_pid',
                                'pipe_client_pid')}
                            ready['version'] = 'workload-r002-worker-ready-v1'
                            frames = [line for line in result['stderr'].splitlines(keepends=True)
                                      if line.startswith(WORKLOAD.GRANT_PREFIX)]
                            frame = WORKLOAD.GRANT_PREFIX + WORKLOAD.encode(ready)
                            self.assertEqual(frames, [frame]
                                * (2 if name == 'duplicate-ready' else 1))
        finally:
            WORKLOAD.ProcessIdentity.close = original_close



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
