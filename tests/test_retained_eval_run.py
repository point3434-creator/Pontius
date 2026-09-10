"""The recorder's observable contracts, using real files and controlled child processes."""
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import signal
import sys
import tempfile
import threading
from concurrent.futures import ThreadPoolExecutor
from contextlib import redirect_stderr
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / 'tools/retained_eval_run.py'
SPEC = importlib.util.spec_from_file_location('retained_runner_tests', PATH)
RUNNER = None
if PATH.exists():
    RUNNER = importlib.util.module_from_spec(SPEC)
    SPEC.loader.exec_module(RUNNER)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def encoded(value):
    return (json.dumps(value, sort_keys=True) + '\n').encode()


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(RUNNER, 'the shared evidence recorder is not implemented')
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.run = self.root / 'experiments/results/runs/new'
        self.run.mkdir(parents=True)
        self.before = b'{"old":true}\n'
        (self.root / 'execution_journal.jsonl').write_bytes(self.before)

    def record(self):
        (self.run / 'result.json').write_bytes(b'{"answer":42}\n')
        (self.run / 'runtimes.json').write_bytes(b'[]\n')
        row = dict(source_commit='a' * 40, source_verified=True,
                   output='experiments/results/runs/new/result.json',
                   output_sha256=digest((self.run / 'result.json').read_bytes()),
                   runtimes_sha256=digest(b'[]\n'))
        raw = encoded(row)
        (self.root / 'execution_journal.jsonl').write_bytes(self.before + raw)
        return raw

    def test_inventory_contains_every_nested_file_and_exact_bytes(self):
        (self.run / 'host-inputs').mkdir()
        (self.run / 'host-inputs/ leading name.json').write_bytes(b'payload')
        (self.run / 'result.json').write_bytes(b'{}')
        self.assertEqual(RUNNER.inventory(self.run), [
            dict(path='host-inputs/ leading name.json', bytes=7, sha256=digest(b'payload')),
            dict(path='result.json', bytes=2, sha256=digest(b'{}'))])

    def test_no_files_cannot_be_a_complete_inventory(self):
        with self.assertRaises(ValueError):
            RUNNER.inventory(self.run)

    def test_enumeration_error_never_returns_a_partial_list(self):
        (self.run / 'host-inputs').mkdir()
        (self.run / 'result.json').write_bytes(b'{}')
        original = os.scandir

        def fault(path):
            if Path(path).name == 'host-inputs':
                raise OSError('directory enumeration failed')
            return original(path)

        with patch.object(RUNNER.os, 'scandir', side_effect=fault):
            with self.assertRaises(OSError):
                RUNNER.inventory(self.run)

    def test_file_read_error_never_returns_success(self):
        (self.run / 'result.json').write_bytes(b'{}')
        with patch.object(RUNNER, 'file_identity', side_effect=OSError('read failed')):
            with self.assertRaises(OSError):
                RUNNER.inventory(self.run)

    def test_links_are_refused_not_silently_omitted(self):
        # Junction/reparse detection is also required on Windows without symlink privilege.
        (self.run / 'result.json').write_bytes(b'{}')
        with patch.object(RUNNER, 'is_link', return_value=True):
            with self.assertRaises(ValueError):
                RUNNER.inventory(self.run)

    def test_exact_new_row_is_copied_without_rewriting(self):
        raw = self.record().replace(b'\n', b'\r\n')
        (self.root / 'execution_journal.jsonl').write_bytes(self.before + raw)
        copied, run = RUNNER.attribute(self.root, self.before, 'a' * 40, set())
        self.assertEqual(copied, raw)
        self.assertEqual(run, self.run)

    def test_old_journal_rewrite_is_not_one_new_row(self):
        self.record()
        path = self.root / 'execution_journal.jsonl'
        path.write_bytes(path.read_bytes().replace(b'true', b'null', 1))
        with self.assertRaises(ValueError):
            RUNNER.attribute(self.root, self.before, 'a' * 40, set())

    def test_absent_extra_wrong_source_and_changed_output_are_refused(self):
        raw = self.record()
        journal = self.root / 'execution_journal.jsonl'
        for tail in (b'', raw + raw, raw.replace(b'a' * 40, b'b' * 40)):
            with self.subTest(tail=tail):
                journal.write_bytes(self.before + tail)
                with self.assertRaises(ValueError):
                    RUNNER.attribute(self.root, self.before, 'a' * 40, set())
        journal.write_bytes(self.before + raw)
        (self.run / 'result.json').write_bytes(b'changed')
        with self.assertRaises(ValueError):
            RUNNER.attribute(self.root, self.before, 'a' * 40, set())

    def test_old_run_or_another_unattributed_run_cannot_pass(self):
        self.record()
        with self.assertRaises(ValueError):
            RUNNER.attribute(self.root, self.before, 'a' * 40, {'new'})
        (self.run.parent / 'orphan').mkdir()
        with self.assertRaises(ValueError):
            RUNNER.attribute(self.root, self.before, 'a' * 40, set())

    def test_missing_runtime_identity_is_refused(self):
        self.record()
        (self.run / 'runtimes.json').unlink()
        with self.assertRaises((ValueError, OSError)):
            RUNNER.attribute(self.root, self.before, 'a' * 40, set())

    def test_create_only_output_preserves_existing_evidence(self):
        target = self.root / 'record.json'
        target.write_bytes(b'original')
        with self.assertRaises(FileExistsError):
            RUNNER.write_new(target, b'replacement')
        self.assertEqual(target.read_bytes(), b'original')

    def test_child_failure_precedes_evidence_failure(self):
        self.assertEqual(RUNNER.exit_status(7, False), 7)
        self.assertEqual(RUNNER.exit_status(0, False), 99)
        self.assertEqual(RUNNER.exit_status(None, False), 99)
        self.assertEqual(RUNNER.exit_status(0, True), 0)


CHILD = r'''import hashlib, json, pathlib, sys
root = pathlib.Path.cwd()
plan_path = pathlib.Path(sys.argv[sys.argv.index('--plan') + 1])
plan_raw = plan_path.read_bytes(); plan = json.loads(plan_raw)
commit = sys.argv[sys.argv.index('--reviewed-commit') + 1]
with (root/'launch-count').open('ab') as stream: stream.write(b'launch\n')
if plan.get('scenario') == 'no-row': sys.exit(0)
run = root/'experiments/results/runs'/('run-' + plan['phase'])
run.mkdir()
(run/'host-inputs').mkdir()
(run/'host-inputs/input.json').write_bytes(b'{"nested":true}\n')
(run/'runtimes.json').write_bytes(b'[]\n')
status = 'failed' if plan.get('scenario') == 'child-failed' else 'completed'
result = dict(status=status, phase=plan['phase'], phase_complete=status=='completed',
              plan_sha256=hashlib.sha256(plan_raw).hexdigest(), cleanup_verified=True,
              resource_state_verified=True)
raw = (json.dumps(result, sort_keys=True)+'\n').encode()
(run/'result.json').write_bytes(raw)
row = dict(source_commit=commit, source_verified=True,
           output=(run/'result.json').relative_to(root).as_posix(),
           output_sha256=hashlib.sha256(raw).hexdigest(),
           runtimes_sha256=hashlib.sha256(b'[]\n').hexdigest())
with (root/'execution_journal.jsonl').open('ab') as stream:
    stream.write((json.dumps(row)+'\n').encode())
sys.stdout.buffer.write(raw)
sys.exit(7 if status=='failed' else 0)
'''


class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(RUNNER)
        self.assertTrue(callable(getattr(RUNNER, 'run', None)), 'shared launch path missing')
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = self.base/'checkout'
        (self.root/'tools').mkdir(parents=True)
        (self.root/'tools/v0a_eval_panel.py').write_text(CHILD, encoding='utf-8')
        (self.root/'experiments/results/runs').mkdir(parents=True)
        (self.root/'execution_journal.jsonl').write_bytes(b'')
        self.git = os.environ.get('PONTIUS_GIT', 'C:/Program Files/Git/cmd/git.exe')
        self.git_call('init', '-q')
        self.git_call('add', 'tools/v0a_eval_panel.py')
        self.git_call('-c', 'user.name=Runner fixture', '-c', 'user.email=fixture@example.invalid',
                      'commit', '-qm', 'Private test fixture')
        self.commit = self.git_call('rev-parse', 'HEAD').decode().strip()
        self.git_call('checkout', '-q', '--detach')
        self.records = self.base/'records'
        self.plan = dict(phase='solve', inputs={}, prerequisites={},
                         resource=dict(seconds=10, memory_mib=128), runtime=dict(python='3.14.6'))
        self.binding = dict(version='pontius-eval-launch-v1', root=str(self.root),
                            retained_root=str(self.base/'retained'), mode='rehearsal',
                            source_commit=self.commit, python=sys.executable, git=self.git,
                            records=str(self.records),
                            authorization=str(self.base/'authorization.json'),
                            runner_sha256=digest(PATH.read_bytes()))
        self.binding_path = self.base/'binding.json'
        self.refresh()

    def git_call(self, *args):
        return subprocess.run([self.git, '-c', f'safe.directory={self.root}',
                               '-C', str(self.root), *args], check=True,
                              capture_output=True).stdout

    def refresh(self):
        path = self.root/'plan.json'
        path.write_bytes(encoded(self.plan))
        self.binding['plan'] = dict(path=str(path), sha256=digest(path.read_bytes()))
        self.binding['baseline'] = dict(
            journal_sha256=digest((self.root/'execution_journal.jsonl').read_bytes()),
            run_directories=sorted(
                p.name for p in (self.root/'experiments/results/runs').iterdir()))
        self.binding_path.write_bytes(encoded(self.binding))
        self.binding_hash = digest(self.binding_path.read_bytes())

    def invoke(self):
        return RUNNER.run(self.binding_path, self.binding_hash)

    def outcome(self):
        return json.loads((self.records/'outcome.json').read_bytes())

    def test_success_records_nested_inventory_and_consumes_claim(self):
        self.assertEqual(self.invoke(), 0)
        self.assertTrue((self.records/'claim.d').is_dir())
        self.assertEqual(self.outcome()['state'], 'verified')
        rows = json.loads((self.records/'inventory.json').read_bytes())['files']
        self.assertEqual({r['path'] for r in rows},
                         {'result.json', 'runtimes.json', 'host-inputs/input.json'})
        self.assertEqual(self.invoke(), 97)
        self.assertEqual((self.root/'launch-count').read_bytes(), b'launch\n')

    def test_second_campaign_uses_the_same_executable_with_a_new_binding(self):
        self.assertEqual(self.invoke(), 0)
        first_hash = digest(PATH.read_bytes())
        self.plan['phase'] = 'export'
        self.records = self.base/'second-records'
        self.binding['records'] = str(self.records)
        self.refresh()
        self.assertEqual(self.invoke(), 0)
        self.assertEqual(digest(PATH.read_bytes()), first_hash)
        self.assertEqual((self.root/'launch-count').read_bytes(), b'launch\nlaunch\n')
        self.assertEqual(self.outcome()['phase'], 'export')

    def test_missing_or_changed_bound_input_refuses_before_claim(self):
        self.plan['inputs'] = {'teacher': dict(path=str(self.base/'missing'), sha256='0'*64)}
        self.refresh()
        self.assertEqual(self.invoke(), 2)
        self.assertFalse((self.records/'claim.d').exists())
        self.assertFalse((self.root/'launch-count').exists())

    def test_missing_environment_refuses_before_claim(self):
        with patch.dict(os.environ, {'TEMP': ''}):
            self.assertEqual(self.invoke(), 2)
        self.assertFalse((self.records/'claim.d').exists())
        self.assertFalse((self.root/'launch-count').exists())

    def test_changed_plan_or_journal_refuses_before_claim(self):
        (self.root/'plan.json').write_bytes(b'changed')
        self.assertEqual(self.invoke(), 2)
        self.refresh()
        (self.root/'execution_journal.jsonl').write_bytes(b'{"unexpected":true}\n')
        self.assertEqual(self.invoke(), 2)
        self.assertFalse((self.records/'claim.d').exists())

    def test_check_only_does_not_claim_or_launch(self):
        self.assertEqual(RUNNER.run(self.binding_path, self.binding_hash, check_only=True), 0)
        self.assertFalse(self.records.exists())
        self.assertFalse((self.root/'launch-count').exists())

    def test_retained_requires_authorization_bound_to_this_document(self):
        self.binding.update(mode='retained', retained_root=str(self.root))
        self.refresh()
        self.assertEqual(self.invoke(), 2)
        authorization = Path(self.binding['authorization'])
        authorization.write_bytes(encoded(dict(binding_sha256='0'*64, controller_text='I approve')))
        self.assertEqual(self.invoke(), 2)
        authorization.write_bytes(encoded(dict(binding_sha256=self.binding_hash,
                                                controller_text='I approve this test fixture')))
        self.assertEqual(self.invoke(), 0)

    def test_child_failure_keeps_its_status_even_with_failed_inventory(self):
        self.plan['scenario'] = 'child-failed'
        self.refresh()
        with patch.object(RUNNER, 'inventory', side_effect=OSError('enumeration failed')):
            self.assertEqual(self.invoke(), 7)
        self.assertEqual(self.outcome()['state'], 'incomplete')

    def test_capture_flush_failure_does_not_erase_nonzero_child_exit(self):
        self.plan['scenario'] = 'child-failed'
        self.refresh()
        original = Path.open

        class FailedFlush:
            def __init__(self, stream):
                self.stream = stream

            def __enter__(self):
                return self

            def __exit__(self, *args):
                self.stream.close()

            def fileno(self):
                return self.stream.fileno()

            def flush(self):
                raise OSError('capture flush failed')

        def capture(path, mode='r', *args, **kwargs):
            stream = original(path, mode, *args, **kwargs)
            return FailedFlush(stream) if path.name == 'stdout.json' and mode == 'xb' else stream

        with patch.object(Path, 'open', capture):
            self.assertEqual(self.invoke(), 7)
        self.assertEqual(self.outcome()['child_exit'], 7)
        self.assertEqual(self.outcome()['state'], 'incomplete')

    def test_failed_child_with_complete_evidence_is_not_a_verified_success(self):
        self.plan['scenario'] = 'child-failed'
        self.refresh()
        self.assertEqual(self.invoke(), 7)
        self.assertEqual(self.outcome()['state'], 'failed')
        self.assertTrue(self.outcome()['evidence_complete'])

    def test_zero_child_without_journal_is_incomplete(self):
        self.plan['scenario'] = 'no-row'
        self.refresh()
        self.assertEqual(self.invoke(), 99)
        self.assertEqual(self.outcome()['state'], 'incomplete')

    def test_inventory_fault_cannot_record_success(self):
        with patch.object(RUNNER, 'inventory', side_effect=OSError('enumeration failed')):
            self.assertEqual(self.invoke(), 99)
        self.assertEqual(self.outcome()['state'], 'incomplete')
        self.assertFalse((self.records/'inventory.json').exists())

    def test_start_record_failure_starts_no_child(self):
        original = RUNNER.write_new

        def fail_start(path, raw):
            if path.name == 'start.json':
                raise OSError('start record failed')
            return original(path, raw)

        with patch.object(RUNNER, 'write_new', side_effect=fail_start):
            self.assertEqual(self.invoke(), 98)
        self.assertTrue((self.records/'claim.d').exists())
        self.assertFalse((self.root/'launch-count').exists())

    def test_capture_open_failure_starts_no_child(self):
        original = Path.open

        def refuse_capture(path, mode='r', *args, **kwargs):
            if path.name == 'stderr.txt' and mode == 'xb':
                raise OSError('capture cannot be created')
            return original(path, mode, *args, **kwargs)

        with patch.object(Path, 'open', refuse_capture):
            self.assertEqual(self.invoke(), 99)
        self.assertFalse((self.root/'launch-count').exists())
        self.assertEqual(self.outcome()['state'], 'incomplete')

    def test_interrupt_before_process_creation_does_not_start_child(self):
        original = RUNNER.write_new
        handler = signal.getsignal(signal.SIGINT)

        def interrupt_after_start(path, raw):
            original(path, raw)
            if path.name == 'start.json':
                signal.raise_signal(signal.SIGINT)

        with patch.object(RUNNER, 'write_new', side_effect=interrupt_after_start):
            self.assertEqual(self.invoke(), 99)
        self.assertFalse((self.root/'launch-count').exists())
        self.assertTrue((self.records/'claim.d').is_dir())
        self.assertEqual(signal.getsignal(signal.SIGINT), handler)

    def test_launch_failure_is_recorded_and_never_retried(self):
        with patch.object(RUNNER, 'launch', side_effect=OSError('cannot start child')):
            self.assertEqual(self.invoke(), 99)
        self.assertIsNone(self.outcome()['child_exit'])
        self.assertEqual(self.invoke(), 97)

    def test_finalization_interrupt_cannot_return_success_or_replace_child_failure(self):
        signals = [signal.SIGINT, signal.SIGBREAK]
        for signum in signals:
            for failed in (False, True):
                for boundary in ('before-open', 'during-fsync'):
                    with self.subTest(signal=signum, child_failed=failed, boundary=boundary):
                        case = RunnerTests()
                        case.setUp()
                        try:
                            if failed:
                                case.plan['scenario'] = 'child-failed'
                                case.refresh()
                            original, fsync = RUNNER.write_new, RUNNER.os.fsync
                            handler = signal.getsignal(signum)

                            def interrupt_flush(fd):
                                signal.raise_signal(signum)
                                return fsync(fd)

                            def interrupt_publication(path, raw):
                                if path.name == 'outcome.json':
                                    if boundary == 'before-open':
                                        signal.raise_signal(signum)
                                    else:
                                        with patch.object(RUNNER.os, 'fsync', interrupt_flush):
                                            return original(path, raw)
                                return original(path, raw)

                            diagnostic = io.StringIO()
                            with redirect_stderr(diagnostic), patch.object(
                                    RUNNER, 'write_new', side_effect=interrupt_publication):
                                self.assertEqual(case.invoke(), 7 if failed else 99)
                            self.assertIn('FINALIZATION INTERRUPTED', diagnostic.getvalue())
                            self.assertEqual(signal.getsignal(signum), handler)
                            if boundary == 'before-open':
                                self.assertFalse((case.records/'outcome.json').exists())
                            self.assertTrue((case.records/'claim.d').is_dir())
                            self.assertEqual(case.invoke(), 97)
                            self.assertEqual((case.root/'launch-count').read_bytes(), b'launch\n')
                        finally:
                            case.doCleanups()

    def test_final_record_failure_returns_failure(self):
        original = RUNNER.write_new

        def fail_end(path, raw):
            if path.name == 'outcome.json':
                raise OSError('end record failed')
            return original(path, raw)

        with patch.object(RUNNER, 'write_new', side_effect=fail_end):
            self.assertEqual(self.invoke(), 99)
        self.assertEqual((self.root/'launch-count').read_bytes(), b'launch\n')

    def test_two_callers_pass_preflight_but_only_one_can_launch(self):
        original = RUNNER.preflight
        barrier = threading.Barrier(2, timeout=20)

        def together(*args):
            prepared = original(*args)
            barrier.wait()
            return prepared

        with patch.object(RUNNER, 'preflight', side_effect=together):
            with ThreadPoolExecutor(max_workers=2) as pool:
                futures = [pool.submit(self.invoke) for _ in range(2)]
                self.assertEqual(sorted(f.result(timeout=30) for f in futures), [0, 97])
        self.assertEqual((self.root/'launch-count').read_bytes(), b'launch\n')


class PhaseCompatibilityTests(unittest.TestCase):
    def test_two_campaigns_through_cli_preserve_retained_teacher_and_host_outcomes(self):
        """Small rehearsal clones only; no packet or retained-run authorization is consumed."""
        git = os.environ['PONTIUS_GIT']
        base = json.loads((ROOT/'tests/fixtures/eval_panel/plan-capacity.json').read_bytes())
        # Reference values read from retained teacher c3ffab403eb7e939...956b3e3,
        # run cf3bcdda9eed4031938c214959b1e10c; not calculated with the implementation.
        expected = [('ThKc', 1962, 3924, 'raise-to-2'), ('8h9c', 580, 1160, 'raise-to-2')]
        (ROOT/'tmp').mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=ROOT/'tmp') as temp:
            parent = Path(temp)
            checkout = parent/'snapshot'
            subprocess.run([git, 'clone', '--shared', '--no-checkout', str(ROOT), str(checkout)],
                           check=True, capture_output=True)
            commit = subprocess.run([git, '-c', f'safe.directory={ROOT}', '-C', str(ROOT),
                                     'rev-parse', 'HEAD'], check=True,
                                    capture_output=True).stdout.decode().strip()
            subprocess.run([git, '-C', str(checkout), 'checkout', '--detach', commit],
                           check=True, capture_output=True)
            for count in (1, 2):
                previous_dir = None
                for phase in ('solve', 'export', 'agreement'):
                    plan = json.loads(json.dumps(base))
                    plan.update(version='pontius-eval-panel-completion-plan-v1', phase=phase,
                                coverage='test-subset', pool_count=count,
                                prerequisites={}, inputs={},
                                resource=dict(seconds=90, memory_mib=3072))
                    if previous_dir is not None:
                        names = {'teacher': 'teacher.json', 'producer_result': 'result.json'}
                        if phase == 'agreement':
                            names['blueprint'] = 'blueprint.json'
                        plan['inputs'] = {
                            key: dict(path=str(previous_dir/name),
                                      sha256=digest((previous_dir/name).read_bytes()))
                            for key, name in names.items()}
                    if phase == 'agreement':
                        plan['witness_bank'] = dict(seed_start='0'*64, seed_count=2048,
                            indices=list(range(16)), holdout_seed_start='f'*64,
                            holdout_seed_count=1, sizing_rationale=
                            'Finite regression bank; actual census gates completion.')
                    plan_path = checkout/'runner-plan.json'
                    plan_path.write_bytes(encoded(plan))
                    records = parent/f'records-{count}-{phase}'
                    config = dict(version='pontius-eval-launch-v1', mode='rehearsal',
                        root=str(checkout), retained_root=str(parent/'never-invoked-retained'),
                        source_commit=commit, python=sys.executable, git=git,
                        plan=dict(path=str(plan_path), sha256=digest(plan_path.read_bytes())),
                        records=str(records), authorization=str(parent/'absent-authorization.json'),
                        baseline=dict(journal_sha256=digest(
                            (checkout/'execution_journal.jsonl').read_bytes()),
                            run_directories=sorted(RUNNER.run_directories(checkout))),
                        runner_sha256=digest(PATH.read_bytes()))
                    binding = parent/'binding.json'
                    binding.write_bytes(encoded(config))
                    ran = subprocess.run([sys.executable, '-I', '-B', str(PATH), '--binding',
                                          str(binding), '--sha256', digest(binding.read_bytes())],
                                         capture_output=True, timeout=150)
                    if ran.returncode and (records/'outcome.json').exists():
                        failure = json.loads((records/'outcome.json').read_bytes())
                        if 'run_directory' in failure:
                            detail = json.loads(
                                (Path(failure['run_directory'])/'result.json').read_bytes())
                            failure['child_detail'] = {key: detail.get(key) for key in
                                ('status', 'error', 'errors', 'phase', 'worker_exit_code')}
                            failure['host_attempts'] = [row for row in detail['observations']
                                                       if row.get('kind') == 'host_attempt']
                        (ROOT/'tmp/runner-compatibility-failure.json').write_bytes(encoded(failure))
                        self.fail(json.dumps(failure))
                    self.assertEqual(ran.returncode, 0, ran.stdout + ran.stderr + (
                        (records/'outcome.json').read_bytes()
                        if (records/'outcome.json').exists() else b''))
                    outcome = json.loads((records/'outcome.json').read_bytes())
                    directory = Path(outcome['run_directory'])
                    result = json.loads((directory/'result.json').read_bytes())
                    self.assertTrue(result['phase_complete'])
                    if phase == 'solve':
                        teacher = json.loads((directory/'teacher.json').read_bytes())
                        observed = [(row['hand'], row['check_total'], row['bet_total'],
                                     row['action'])
                                    for row in teacher['rows']]
                        self.assertEqual(observed, expected[:count])
                    elif phase == 'export':
                        self.assertEqual((directory/'teacher.json').read_bytes(),
                                         (previous_dir/'teacher.json').read_bytes())
                        membership = next(row['report'] for row in result['observations']
                                          if row.get('kind') == 'membership')
                        self.assertEqual(membership['hits'], count)
                        self.assertEqual(membership['disagreements'], 0)
                    else:
                        accounting = result['agreement_accounting']
                        self.assertEqual(accounting['primary']['hits'], count)
                        self.assertEqual(accounting['scheduled_attempts'], count+3)
                        self.assertEqual(accounting['missing_outcomes'], 0)
                        self.assertEqual(accounting['missing_pool_hands'], [])
                        files = json.loads((records/'inventory.json').read_bytes())['files']
                        self.assertIn('host-inputs/host-input.json', {row['path'] for row in files})
                    previous_dir = directory


if __name__ == '__main__':
    unittest.main()
