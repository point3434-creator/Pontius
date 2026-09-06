"""Native ownership and independently corrupted wire controls for the finite host."""
from __future__ import annotations

import base64
import ctypes
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[1]
TOOL = REPO / 'tools/v0a_table_host.py'
FIXTURES = REPO / 'tests/fixtures/table_host'
SESSION = 'pontius-v0a-table-host-v1-correctness-boundary'
LOAD = """
import importlib.util, sys
from pathlib import Path
spec = importlib.util.spec_from_file_location(
    'boundary_host', Path.cwd() / 'tools/v0a_table_host.py')
h = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = h
spec.loader.exec_module(h)
"""


def load_tool():
    spec = importlib.util.spec_from_file_location('boundary_native_host', TOOL)
    host = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = host
    spec.loader.exec_module(host)
    return host


def run_script(script, arguments=()):
    environment = {k: v for k, v in os.environ.items()
                   if not k.upper().startswith(('PYTHON', 'GIT_'))}
    return subprocess.run([sys.executable, '-B', '-P', '-X',
                          'int_max_str_digits=' + str(sys.get_int_max_str_digits()),
                          '-c', LOAD + script, *arguments],
                          cwd=REPO, env=environment, capture_output=True, timeout=90)


def cli(table=None):
    return ['--table', str(table or FIXTURES / 'fold_table.json'), '--blueprint',
            str(REPO / 'tests/fixtures/event_adapter/fold_blueprint.json'),
            '--session-id', SESSION]


def bootstrap(body):
    return ("import os,sys\ngate=os.read(0,1)\n"
            "if gate != b'G': sys.exit(91)\n" + body)


def mutated_bootstrap(kind, mutation):
    # The sealed adapter runs unchanged. Only its actual stdout byte emission is controlled.
    return bootstrap("""
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(sys.executable)),
                            'Lib', 'site-packages'))
import json, runpy
real_write = os.write
def controlled_write(fd, raw):
    if fd == 1:
        row = json.loads(raw)
        if row['type'] == KIND:
            exec(MUTATION)
            changed = (json.dumps(row, separators=(',', ':')) + '\\n').encode()
            real_write(fd, changed)
            return len(raw)
    return real_write(fd, raw)
os.write = controlled_write
sys.argv = sys.argv[1:]
runpy.run_path(sys.argv[0], run_name='__main__')
""".replace('KIND', repr(kind)).replace('MUTATION', repr(mutation)))


class WireMutationTests(unittest.TestCase):
    def corrupted(self, kind, mutation, expected, actions):
        script = 'h.BOOTSTRAP = ' + repr(mutated_bootstrap(kind, mutation))
        result = run_script(script + '\nraise SystemExit(h.main(sys.argv[1:]))\n', cli())
        self.assertEqual(result.returncode, 1, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report['status'], 'failed', report)
        self.assertEqual(report['failure_reason'], expected, report)
        self.assertIsNone(report['settlement'])
        self.assertEqual(len(report['applied_actions']), actions, report)
        self.assertEqual([a['index'] for a in report['applied_actions']], list(range(actions)))
        self.assertIs(type(report['child_exit_code']), int)
        raw = base64.b64decode(report['child_stdout_base64'], validate=True)
        self.assertIn(kind.encode(), raw)
        if actions:
            self.assertEqual(report['applied_actions'][0], dict(index=0, seat=3,
                street='preflop', action=dict(kind='raise', raise_to=8), origin='bot'))
        return report

    def test_ready_rejects_each_false_identity_and_exact_type(self):
        for field, value in [('source_commit', '0' * 40), ('source_manifest_sha256', '0' * 64),
                             ('blueprint_artifact_sha256', '0' * 64),
                             ('blueprint_sha256', '0' * 64), ('evidentiary', 0),
                             ('session_id', 'wrong-session'), ('protocol', 'wrong-protocol')]:
            with self.subTest(field=field):
                self.corrupted('ready', f'row[{field!r}] = {value!r}', 'protocol_invalid', 0)

    def test_wire_json_rejects_invalid_encoding_members_numbers_and_depth(self):
        cases = [b'\xef\xbb\xbf{}\n', b'{"a":1,"a":2}\n', b'{"a":NaN}\n',
                 b'{}\r\n', b'{"a":"\xff"}\n', b'[' * 9 + b']' * 9 + b'\n',
                 b'{"a":' + b'9' * 641 + b'}\n', b'{"type":"ready"}\n']
        for raw in cases:
            with self.subTest(raw=raw[:80]):
                child = bootstrap('os.write(1,' + repr(raw) + '); os.read(0,1)')
                result = run_script('h.BOOTSTRAP = ' + repr(child)
                                    + '\nraise SystemExit(h.main(sys.argv[1:]))', cli())
                report = json.loads(result.stdout)
                self.assertEqual(result.returncode, 1, result.stderr)
                self.assertEqual(report['failure_reason'], 'protocol_invalid')
                self.assertEqual(report['applied_actions'], [])
                self.assertEqual(base64.b64decode(report['child_stdout_base64']), raw)
        for mutation in ("row['unknown'] = 1", "del row['evidentiary']"):
            with self.subTest(mutation=mutation):
                self.corrupted('ready', mutation, 'protocol_invalid', 0)

    def test_action_rejected_before_any_application(self):
        for mutation, code in [
            ("row['action_index'] = True", 'protocol_invalid'),
            ("row['seat'] = 4", 'protocol_invalid'),
            ("row['street'] = 'flop'", 'protocol_invalid'),
            ("row['hand_id'] = 'wrong'", 'protocol_invalid'),
            ("row['action'] = {'kind':'raise','raise_to':True}", 'protocol_invalid'),
            ("row['action'] = {'kind':'check','raise_to':None}", 'action_invalid'),
            ("row['action'] = {'kind':'raise','raise_to':3}", 'action_invalid')]:
            with self.subTest(mutation=mutation):
                self.corrupted('action', mutation, code, 0)

    def test_decision_mismatch_keeps_exactly_one_already_applied_action(self):
        for field, value in [('state_before_sha256', '0' * 64),
                             ('state_after_sha256', '0' * 64),
                             ('visible_cards_sha256', '0' * 64),
                             ('blueprint_sha256', '0' * 64), ('event_index', 1),
                             ('street_action_index', 2),
                             ('selected_action', dict(kind='call', raise_to=None))]:
            with self.subTest(field=field):
                self.corrupted('event_result', f"row['decision'][{field!r}] = {value!r}",
                               'state_mismatch', 1)

    def test_decision_invalid_fields_are_not_diagnostic_exemptions(self):
        for mutation in [
            "row['decision']['event_index'] = False",
            "row['decision']['selection_reason'] = 'invented'",
            "row['decision']['spine_reason'] = 'invented'",
            "row['decision']['preparation_use']['credited_seconds'] = False",
            "row['decision']['preparation_use']['artifact_sha256s'] = ['0'*64]",
            "row['decision']['timing']['wall_start_ns'] = True",
            "row['decision']['timing']['work_cutoff_crossed'] = True",
            "row['decision']['timing']['response_compute_seconds'] = 100.0",
            "row['decision']['timing']['elapsed_ns'] += 1",
            "row['decision']['timing']['response_uninstrumented_seconds'] = 0",
            "row['decision']['timing']['interruption_reason'] = 'output_failed'"]:
            with self.subTest(mutation=mutation):
                self.corrupted('event_result', mutation, 'protocol_invalid', 1)

    def test_settlement_wrong_amount_stack_or_eligible_seat_is_rejected(self):
        for mutation in ["row['settlement']['payouts'][3] = 6",
                         "row['settlement']['final_stacks'][3] = 204",
                         "row['settlement']['pots'][0]['amount'] = 6",
                         "row['settlement']['pots'][0]['seats'] = [2,3]"]:
            with self.subTest(mutation=mutation):
                self.corrupted('hand_result', mutation, 'settlement_mismatch', 6)

    def test_closing_shape_timing_and_accounting_must_all_be_valid(self):
        for kind, mutation in [
            ('hand_result', "row['complete'] = 1"),
            ('hand_result', "row['interrupted_response_count'] = False"),
            ('hand_result', "row['preparation_compute_seconds'] = 0"),
            ('hand_result', "row['settlement']['payouts'][0] = False"),
            ('hand_result', "row['rank_source'] = 'host_supplied'"),
            ('session_result', "row['accounting_complete'] = False"),
            ('session_result', "row['terminal_publication_compute_seconds'] = None"),
            ('session_result', "row['accounting_scope'] = 'invented'"),
            ('session_result', "row['evidentiary'] = 0"),
            ('session_result', "row['secondary_failures'] = ['invented']")]:
            with self.subTest(kind=kind, mutation=mutation):
                self.corrupted(kind, mutation, 'protocol_invalid', 6)

    def test_failed_session_overrides_good_hand_without_erasing_actions(self):
        self.corrupted('session_result', "row['status'] = 'failed'", 'child_failed', 6)

    def test_nonzero_exit_overrides_good_hand_and_session(self):
        original = mutated_bootstrap('session_result', 'pass')
        changed = original.replace("runpy.run_path(sys.argv[0], run_name='__main__')",
            "try:\n    runpy.run_path(sys.argv[0], run_name='__main__')\nfinally:\n    os._exit(7)")
        result = run_script('h.BOOTSTRAP = ' + repr(changed)
                            + '\nraise SystemExit(h.main(sys.argv[1:]))', cli())
        report = json.loads(result.stdout)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(report['failure_reason'], 'child_failed')
        self.assertEqual(report['child_exit_code'], 7)
        self.assertEqual(len(report['applied_actions']), 6)
        self.assertIsNone(report['settlement'])

    def test_extra_frame_after_completed_session_prevents_success(self):
        self.corrupted('session_result', "real_write(fd, raw)", 'protocol_invalid', 6)

    def test_valid_failed_event_before_action_is_child_failure(self):
        mutation = """
failure = dict(hand_id=row['hand_id'], event_index=0, action_index=1,
               code='invalid_blueprint_entry', delivery_status='not_attempted',
               delivered_action=None, timing=None)
protocol, session = row['protocol'], row['session_id']
row.clear()
row.update(protocol=protocol, session_id=session, type='event_result', event_index=0,
           status='failed', decision=None, failure=failure)
"""
        self.corrupted('action', mutation, 'child_failed', 0)

    def test_valid_failed_event_with_exceeded_timing_keeps_delivered_action(self):
        mutation = """
decision = row['decision']
timing = decision['timing']
timing.update(wall_start_ns=0, last_valid_observation_ns=15000000001,
              emission_observed_ns=15000000001, elapsed_ns=15000000001,
              response_compute_seconds=15.000000001, response_uninstrumented_seconds=0.0,
              work_cutoff_crossed=True, deadline_crossed=True)
row.update(status='failed', decision=None, failure=dict(hand_id=decision['hand_id'],
    event_index=0, action_index=1, code='action_deadline_exceeded', delivery_status='accepted',
    delivered_action=decision['selected_action'], timing=timing))
"""
        self.corrupted('event_result', mutation, 'child_failed', 1)

    def test_duplicate_action_cannot_apply_twice(self):
        self.corrupted('action', 'real_write(fd, raw)', 'protocol_invalid', 1)

    def test_unsolicited_action_after_opponent_event_cannot_mutate_table(self):
        mutation = """
if row['status'] == 'accepted':
    protocol, session = row['protocol'], row['session_id']
    row.clear()
    row.update(protocol=protocol, session_id=session, type='action', hand_id=session,
               action_index=2, seat=3, street='preflop', action=dict(kind='call', raise_to=None))
"""
        self.corrupted('event_result', mutation, 'protocol_invalid', 2)

    def test_missing_action_does_not_get_inferred_from_decision(self):
        script = mutated_bootstrap('action', 'pass').replace(
            'real_write(fd, changed)', 'None')
        result = run_script('h.BOOTSTRAP = ' + repr(script)
                            + '\nraise SystemExit(h.main(sys.argv[1:]))', cli())
        report = json.loads(result.stdout)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(report['failure_reason'], 'protocol_invalid')
        self.assertEqual(report['applied_actions'], [])
        self.assertIsNone(report['settlement'])


class AdmissionDriftTests(unittest.TestCase):
    def test_help_and_abbreviated_flags_refuse_with_one_json_result(self):
        for arguments in (['--help'], ['--tabl', *cli()[1:]]):
            with self.subTest(arguments=arguments):
                result = run_script('raise SystemExit(h.main(sys.argv[1:]))', arguments)
                self.assertEqual(result.returncode, 1, result.stderr)
                self.assertTrue(result.stdout.startswith(b'{'), result.stdout)
                self.assertEqual(result.stdout.count(b'\n'), 1)
                report = json.loads(result.stdout)
                self.assertEqual(report['failure_reason'], 'input_invalid')
                self.assertIsNone(report['child_exit_code'])
                self.assertEqual(report['applied_actions'], [])

    def test_source_drift_after_good_child_hand_cannot_publish_settlement(self):
        target = REPO / 'src/pontius/__boundary_unadmitted_control__.txt'
        self.assertFalse(target.exists())
        marker = b'finite controlled source drift\n'
        mutation = f"open({str(target)!r}, 'xb').write({marker!r})"
        script = 'h.BOOTSTRAP = ' + repr(mutated_bootstrap('session_result', mutation))
        try:
            result = run_script(script + '\nraise SystemExit(h.main(sys.argv[1:]))', cli())
            report = json.loads(result.stdout)
            self.assertEqual(target.read_bytes(), marker)
            self.assertEqual(result.returncode, 1, result.stderr)
            self.assertEqual(report['failure_reason'], 'source_invalid')
            self.assertEqual(len(report['applied_actions']), 6)
            self.assertIsNone(report['settlement'])
        finally:
            if target.exists() and target.read_bytes() == marker:
                target.unlink()

    def test_cached_pontius_is_refused_before_process_launch(self):
        for name in ('pontius', 'pontius.no_limit_betting'):
            with self.subTest(name=name):
                result = run_script("sys.path.insert(0, str(Path.cwd() / 'src'))\n"
                    + '__import__(' + repr(name) + ')\n'
                    + 'raise SystemExit(h.main(sys.argv[1:]))', cli())
                report = json.loads(result.stdout)
                self.assertEqual(result.returncode, 1, result.stderr)
                self.assertEqual(report['failure_reason'], 'source_invalid')
                self.assertIsNone(report['child_exit_code'])
                self.assertEqual(report['child_stdout_base64'], '')

    def test_source_population_drift_and_wrong_import_origin_are_refused(self):
        controls = ["""
import tempfile, os
fd, name = tempfile.mkstemp(prefix='boundary_unadmitted_', suffix='.py',
                          dir=Path.cwd()/'src/pontius')
os.close(fd)
try:
    source.check()
finally:
    os.unlink(name)
""", """
source.load()
sys.modules['pontius.no_limit_betting'].__file__ = str(Path.cwd()/'wrong.py')
source.check()
"""]
        for control in controls:
            with self.subTest(control=control):
                script = "source=h.Source(Path.cwd())\ntry:\n"
                script += ''.join('    ' + line + '\n' for line in control.splitlines())
                script += ("except h.HostRefusal as error:\n    print(error.code)\n"
                           "else:\n    sys.exit(9)\n")
                result = run_script(script)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout.strip(), b'source_invalid')

    def test_input_drift_after_good_child_hand_cannot_publish_settlement(self):
        for which in ('table', 'blueprint'):
            with self.subTest(which=which), tempfile.TemporaryDirectory() as temporary:
                table = Path(temporary) / 'table.json'
                policy = Path(temporary) / 'blueprint.json'
                table.write_bytes((FIXTURES / 'fold_table.json').read_bytes())
                policy.write_bytes((REPO / 'tests/fixtures/event_adapter/fold_blueprint.json')
                                   .read_bytes())
                target = table if which == 'table' else policy
                mutation = f"open({str(target)!r}, 'ab').write(b'\\n')"
                script = 'h.BOOTSTRAP = ' + repr(mutated_bootstrap('session_result', mutation))
                arguments = cli(table)
                arguments[3] = str(policy)
                result = run_script(script + '\nraise SystemExit(h.main(sys.argv[1:]))', arguments)
                report = json.loads(result.stdout)
                self.assertEqual(result.returncode, 1, result.stderr)
                self.assertEqual(report['failure_reason'], 'input_invalid', report)
                self.assertEqual(len(report['applied_actions']), 6)
                self.assertIsNone(report['settlement'])
                self.assertIn(b'"status":"completed"',
                              base64.b64decode(report['child_stdout_base64']))


class NativeConnectionTests(unittest.TestCase):
    def setUp(self):
        self.host = load_tool()
        self.source = SimpleNamespace(python=Path(sys.executable), repo=REPO,
                                      git=Path(os.environ['PONTIUS_GIT']))
        self.failures = self.host.Failures()

    def connection(self, body):
        with patch.object(self.host, 'BOOTSTRAP', bootstrap(body)):
            conn = self.host.ChildConnection(self.source, FIXTURES / 'empty_blueprint.json',
                                            'fixed-native-control', self.failures)
        self.addCleanup(conn.finish, False)
        return conn

    def assert_stopped(self, conn):
        self.assertIsNotNone(conn.proc.poll())
        self.assertIsNone(conn.job.handle)
        self.assertTrue(all(not t.is_alive() for t in conn.threads))
        self.assertTrue(all(s.closed for s in (conn.proc.stdin, conn.proc.stdout,
                                             conn.proc.stderr)))

    def wait_failure(self, conn):
        limit = time.monotonic() + 5
        while not self.failures.items and time.monotonic() < limit:
            threading.Event().wait(0.01)
        self.assertTrue(self.failures.items)

    def test_gate_precedes_native_assignment_and_job_contains_root_and_grandchild(self):
        assigned = threading.Event()
        real_assign = self.host.Job.assign
        real_send = self.host.ChildConnection.send
        def send(conn, raw, deadline):
            if raw == b'G':
                self.assertTrue(assigned.is_set(), 'bootstrap released before native assignment')
            return real_send(conn, raw, deadline)
        def observe(job, proc):
            # Peek actual kernel pipe before release: no gated application output exists.
            import msvcrt
            api = ctypes.WinDLL('kernel32', use_last_error=True)
            api.PeekNamedPipe.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_ulong,
                                         ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p]
            available = ctypes.c_ulong()
            self.assertTrue(api.PeekNamedPipe(msvcrt.get_osfhandle(proc.stdout.fileno()),
                None, 0, None, ctypes.byref(available), None))
            self.assertEqual(available.value, 0)
            real_assign(job, proc)
            self.assertEqual(job.active(), 1)
            assigned.set()
        descendant = "import os; os.read(0,1)"
        body = ("import subprocess\n"
                "p=subprocess.Popen([sys.executable,'-B','-P','-S','-c'," + repr(descendant)
                + "],stdin=subprocess.PIPE)\n"
                "os.write(1,(str(p.pid)+'\\n').encode())\nos.read(0,1)\n")
        with patch.object(self.host.Job, 'assign', observe), patch.object(
                self.host.ChildConnection, 'send', send):
            conn = self.connection(body)
        self.assertTrue(assigned.is_set())
        descendant_pid = int(conn.receive(time.monotonic() + 5))
        # Venv redirector interpreters can add another owned native process per launch.
        self.assertGreaterEqual(conn.job.active(), 2)
        api = ctypes.WinDLL('kernel32', use_last_error=True)
        api.OpenProcess.argtypes = [ctypes.c_ulong, ctypes.c_int, ctypes.c_ulong]
        api.OpenProcess.restype = ctypes.c_void_p
        api.WaitForSingleObject.argtypes = [ctypes.c_void_p, ctypes.c_ulong]
        api.CloseHandle.argtypes = [ctypes.c_void_p]
        api.IsProcessInJob.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p]
        api.GetHandleInformation.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
        api.GetCurrentProcess.restype = ctypes.c_void_p
        handle = api.OpenProcess(0x100400, False, descendant_pid)
        self.assertTrue(handle)
        try:
            flags = ctypes.c_ulong()
            self.assertTrue(api.GetHandleInformation(conn.job.handle, ctypes.byref(flags)))
            self.assertEqual(flags.value & 1, 0, 'owned Job handle must not be inherited')
            host_belongs = ctypes.c_int()
            self.assertTrue(api.IsProcessInJob(api.GetCurrentProcess(), conn.job.handle,
                                               ctypes.byref(host_belongs)))
            self.assertEqual(host_belongs.value, 0)
            for process_handle in (int(conn.proc._handle), handle):
                belongs = ctypes.c_int()
                self.assertTrue(api.IsProcessInJob(process_handle, conn.job.handle,
                                                   ctypes.byref(belongs)))
                self.assertEqual(belongs.value, 1)
            self.assertEqual(api.WaitForSingleObject(handle, 0), 258)
            conn.finish(False)
            self.assertEqual(api.WaitForSingleObject(handle, 5000), 0)
            self.assert_stopped(conn)
            self.assertNotIn('cleanup_failed', self.failures.items)
        finally:
            api.CloseHandle(handle)

    def test_actual_bootstrap_and_descendants_are_owned_despite_redirector_scheduling(self):
        # Force the redirector's real interpreter to exist before an unsuspended
        # assignment. Suspended creation must instead assign before native resume.
        api = ctypes.WinDLL('kernel32', use_last_error=True)
        api.OpenProcess.argtypes = [ctypes.c_ulong, ctypes.c_int, ctypes.c_ulong]
        api.OpenProcess.restype = ctypes.c_void_p
        api.IsProcessInJob.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p]
        api.TerminateProcess.argtypes = [ctypes.c_void_p, ctypes.c_uint]
        api.WaitForSingleObject.argtypes = [ctypes.c_void_p, ctypes.c_ulong]
        api.CloseHandle.argtypes = [ctypes.c_void_p]
        api.ResumeThread.argtypes = [ctypes.c_void_p]
        api.ResumeThread.restype = ctypes.c_ulong
        real_resume, real_assign = api.ResumeThread, self.host.Job.assign
        real_popen = self.host.subprocess.Popen
        observation, handles, memberships = {}, [], []
        assigned = threading.Event()

        def belongs(handle, job):
            value = ctypes.c_int()
            self.assertTrue(api.IsProcessInJob(handle, job.handle, ctypes.byref(value)))
            return value.value

        def launch(*args, **kwargs):
            observation['flags'] = kwargs.get('creationflags', 0)
            return real_popen(*args, **kwargs)

        def assign(job, process):
            if not observation['flags'] & 4:
                ready, identity = threading.Event(), bytearray()
                def read_identity():
                    try:
                        while not identity.endswith(b'\n') and len(identity) < 30:
                            chunk = process.stderr.read(1)
                            if not chunk:
                                break
                            identity.extend(chunk)
                    finally:
                        ready.set()
                thread = threading.Thread(target=read_identity, daemon=True)
                thread.start()
                self.assertTrue(ready.wait(5), 'actual bootstrap must reach pre-assignment gate')
                self.assertTrue(identity.endswith(b'\n'))
                observation['pre_assignment_bootstrap_pid'] = int(identity)
            real_assign(job, process)
            self.assertEqual(belongs(int(process._handle), job), 1)
            assigned.set()

        def resume(thread_handle):
            self.assertTrue(assigned.is_set(), 'native resume preceded real Job assignment')
            return real_resume(thread_handle)

        descendant = "import os; os.write(1,(str(os.getpid())+'\\n').encode()); os.read(0,1)"
        body = ("import subprocess,json\n"
                "p=subprocess.Popen([sys.executable,'-B','-P','-S','-c'," + repr(descendant)
                + "],stdin=subprocess.PIPE,stdout=subprocess.PIPE)\n"
                "ids=[os.getpid(),p.pid,int(p.stdout.readline())]\n"
                "os.write(1,(json.dumps(ids)+'\\n').encode())\nos.read(0,1)\n")
        fixed = bootstrap(body).replace('gate=os.read(0,1)',
                    "os.write(2,(str(os.getpid())+'\\n').encode())\ngate=os.read(0,1)")
        conn = None
        try:
            with patch.object(self.host, 'BOOTSTRAP', fixed), patch.object(
                    self.host.subprocess, 'Popen', launch), patch.object(
                    self.host.Job, 'assign', assign), patch.object(
                    self.host.ctypes, 'WinDLL', return_value=api), patch.object(
                    api, 'ResumeThread', side_effect=resume):
                conn = self.host.ChildConnection(self.source, FIXTURES / 'empty_blueprint.json',
                                                'fixed-redirector-control', self.failures)
            identities = json.loads(conn.receive(time.monotonic() + 5))
            self.assertEqual(len(identities), 3)
            if 'pre_assignment_bootstrap_pid' in observation:
                self.assertEqual(identities[0], observation['pre_assignment_bootstrap_pid'])
            for pid in dict.fromkeys(identities):
                handle = api.OpenProcess(0x100401, False, pid)
                self.assertTrue(handle)
                handles.append(handle)
                memberships.append(belongs(handle, conn.job))
            self.assertTrue(all(value == 1 for value in memberships),
                            dict(pids=identities, membership=memberships))
        finally:
            # Failed containment must not leave diagnostic processes outside the Job.
            for handle, membership in reversed(list(zip(handles, memberships))):
                if membership == 0 and api.WaitForSingleObject(handle, 0) == 258:
                    api.TerminateProcess(handle, 9)
            if conn is not None:
                conn.finish(False)
            for handle in handles:
                self.assertEqual(api.WaitForSingleObject(handle, 5000), 0)
                api.CloseHandle(handle)
        self.assert_stopped(conn)

    def test_partial_stdout_does_not_extend_absolute_deadline_and_is_captured(self):
        conn = self.connection("os.write(1,b'partial'); os.write(2,b'diagnostic'); os.read(0,1)")
        with self.assertRaises(self.host.HostRefusal) as error:
            conn.receive(time.monotonic() + 0.3)
        self.assertEqual(error.exception.code, 'host_limit')
        self.failures.add(error.exception.code)
        conn.finish(False)
        self.assertEqual(bytes(conn.stdout), b'partial')
        self.assertEqual(bytes(conn.stderr), b'diagnostic')
        self.assertEqual(self.failures.items[0], 'host_limit')
        self.assertIn('protocol_invalid', self.failures.items)
        self.assert_stopped(conn)

    def test_blocked_stdin_write_is_bounded_and_cancelled_by_real_job_termination(self):
        conn = self.connection("os.write(1,b'waiting\\n'); import time; time.sleep(30)")
        self.assertEqual(conn.receive(time.monotonic() + 5), b'waiting\n')
        with self.assertRaises(self.host.HostRefusal) as error:
            conn.send(b'x' * 1048576, time.monotonic() + 0.2)
        self.assertEqual(error.exception.code, 'host_limit')
        self.failures.add(error.exception.code)
        conn.finish(False)
        self.assertEqual(self.failures.items[0], 'host_limit')
        self.assertIn('transport_failed', self.failures.items)
        self.assert_stopped(conn)

    def test_frame_queue_flood_fails_closed_and_retains_raw_prefix(self):
        conn = self.connection("os.write(1,b'{}\\n'*100); os.read(0,1)")
        self.wait_failure(conn)
        conn.finish(False)
        self.assertEqual(self.failures.items[0], 'transport_failed')
        self.assertTrue(bytes(conn.stdout).startswith(b'{}\n' * 9))
        self.assert_stopped(conn)

    def test_stderr_flood_caps_capture_and_marks_truncation(self):
        conn = self.connection("os.write(2,b'z'*70000); os.read(0,1)")
        self.wait_failure(conn)
        conn.finish(False)
        self.assertEqual(self.failures.items[0], 'transport_failed')
        self.assertIs(conn.truncated, True)
        self.assertEqual(bytes(conn.stderr), b'z' * 65536)
        self.assert_stopped(conn)

    def test_stdout_total_cap_is_enforced_even_with_consumed_bounded_frames(self):
        conn = self.connection("for _ in range(513):\n    os.read(0,1)\n"
                               "    os.write(1,b'x'*4095+b'\\n')\nos.read(0,1)")
        for _ in range(512):
            conn.proc.stdin.write(b'R')
            self.assertEqual(conn.receive(time.monotonic() + 5), b'x' * 4095 + b'\n')
        conn.proc.stdin.write(b'R')
        self.wait_failure(conn)
        conn.finish(False)
        self.assertEqual(self.failures.items[0], 'transport_failed')
        self.assertEqual(bytes(conn.stdout), (b'x' * 4095 + b'\n') * 512)
        self.assertIs(conn.truncated, True)
        self.assert_stopped(conn)

    def test_oversized_stdout_frame_is_not_accepted_as_a_complete_frame(self):
        conn = self.connection("os.write(1,b'x'*16384); os.read(0,1)")
        self.wait_failure(conn)
        conn.finish(False)
        self.assertEqual(self.failures.items[0], 'protocol_invalid')
        self.assertEqual(bytes(conn.stdout), b'x' * 16384)
        self.assert_stopped(conn)

    def test_cleanup_api_failure_is_secondary_and_real_close_still_kills_root(self):
        conn = self.connection("os.write(1,b'waiting\\n'); os.read(0,1)")
        self.assertEqual(conn.receive(time.monotonic() + 5), b'waiting\n')
        self.failures.add('state_mismatch')
        with patch.object(conn.job.api, 'TerminateJobObject', return_value=0):
            conn.finish(False)
        self.assertEqual(self.failures.items, ['state_mismatch', 'cleanup_failed'])
        self.assert_stopped(conn)

    def test_reader_io_failure_retains_actual_bytes_and_terminates_owned_root(self):
        real_reader = self.host.ChildConnection.read_stream
        class FailedRead:
            def __init__(self, stream):
                self.stream, self.reads = stream, 0
            def read(self, count):
                self.reads += 1
                if self.reads == 2:
                    raise OSError('controlled next pipe read failure')
                return self.stream.read(count)
        def read(conn, stream, stdout):
            return real_reader(conn, FailedRead(stream) if stdout else stream, stdout)
        with patch.object(self.host.ChildConnection, 'read_stream', read):
            conn = self.connection("os.read(0,1); os.write(1,b'real-prefix\\n'); os.read(0,1)")
        conn.proc.stdin.write(b'R')
        self.wait_failure(conn)
        conn.finish(False)
        self.assertEqual(self.failures.items[0], 'transport_failed')
        self.assertEqual(bytes(conn.stdout), b'real-prefix\n')
        self.assert_stopped(conn)

    def test_child_launch_flags_environment_and_binary_capture_are_real(self):
        body = ("import json\nos.write(1,(json.dumps(dict(flags=[sys.flags.dont_write_bytecode,"
                "sys.flags.safe_path,sys.flags.no_site],env=dict(os.environ)))+'\\n').encode());"
                "os.write(2,b'\\x00\\xff\\r\\n'); os.read(0,1)")
        with patch.dict(os.environ, {'PYTHONSTARTUP': 'untrusted', 'GIT_DIR': 'untrusted',
                                     'PONTIUS_UNDECLARED': 'untrusted'}):
            conn = self.connection(body)
        row = json.loads(conn.receive(time.monotonic() + 5))
        self.assertEqual(row['flags'], [1, True, 1])
        self.assertFalse(any(k.startswith(('PYTHON', 'GIT_')) for k in row['env']))
        self.assertNotIn('PONTIUS_UNDECLARED', row['env'])
        self.assertEqual(row['env']['PONTIUS_GIT'], os.environ['PONTIUS_GIT'])
        conn.finish(False)
        self.assertEqual(bytes(conn.stderr), b'\x00\xff\r\n')
        self.assert_stopped(conn)

    def test_successful_root_with_living_descendant_is_cleanup_failure(self):
        child = 'import time; time.sleep(30)'
        conn = self.connection("import subprocess\np=subprocess.Popen([sys.executable,"
            "'-B','-P','-S','-c'," + repr(child) + "],stdin=subprocess.PIPE)\n"
            "os.write(1,b'root-done\\n')\n")
        self.assertEqual(conn.receive(time.monotonic() + 5), b'root-done\n')
        self.assertEqual(conn.proc.wait(timeout=5), 0)
        self.assertGreater(conn.job.active(), 0)
        conn.finish(True)
        self.assertEqual(self.failures.items, ['cleanup_failed'])
        self.assertEqual(conn.exit_code, 0)
        self.assert_stopped(conn)

    def test_later_successful_native_reap_is_retained_after_first_wait_timeout(self):
        conn = self.connection("os.write(1,b'waiting\\n'); os.read(0,1)")
        self.assertEqual(conn.receive(time.monotonic() + 5), b'waiting\n')
        real_wait, calls = conn.proc.wait, []
        def wait(timeout=None):
            calls.append(timeout)
            if len(calls) == 1:
                raise subprocess.TimeoutExpired(conn.proc.args, timeout)
            return real_wait(timeout=timeout)
        self.failures.add('state_mismatch')
        with patch.object(conn.proc, 'wait', wait):
            conn.finish(False)
        self.assertEqual(len(calls), 2)
        self.assertIs(type(conn.proc.returncode), int)
        self.assertEqual(conn.exit_code, conn.proc.returncode)
        self.assertEqual(self.failures.items, ['state_mismatch', 'cleanup_failed'])
        self.assert_stopped(conn)


class HostFailureRetentionTests(unittest.TestCase):
    def test_native_resume_failures_never_release_and_always_reap_real_root(self):
        script = """
from unittest.mock import patch
owned = []
real_popen, real_resume = h.subprocess.Popen, h.Job.resume
def launch(*args, **kwargs):
    process = real_popen(*args, **kwargs)
    if '-c' in args[0]:
        owned.append(process)
    return process
def controlled_resume(self, process):
    native_close = self.api.CloseHandle
    def close_then_refuse(handle):
        assert native_close(handle)
        return 0
    if CASE in ('close', 'resume_and_close'):
        with patch.object(self.api, 'CloseHandle', side_effect=close_then_refuse):
            if CASE == 'resume_and_close':
                with patch.object(self.api, 'ResumeThread', return_value=0):
                    return real_resume(self, process)
            return real_resume(self, process)
    function, value = {
        'snapshot': ('CreateToolhelp32Snapshot', h.ctypes.c_void_p(-1).value),
        'enumeration': ('Thread32First', 0),
        'open': ('OpenThread', None),
        'owner': ('GetProcessIdOfThread', 0),
        'resume': ('ResumeThread', 0),
    }[CASE]
    with patch.object(self.api, function, return_value=value):
        return real_resume(self, process)
with patch.object(h.subprocess, 'Popen', launch), patch.object(h.Job, 'resume', controlled_resume):
    code = h.main(sys.argv[1:])
assert len(owned) == 1 and owned[0].poll() is not None
assert owned[0].returncode != 0
assert all(stream.closed for stream in (owned[0].stdin, owned[0].stdout, owned[0].stderr))
raise SystemExit(code)
"""
        for case in ('snapshot', 'enumeration', 'open', 'owner', 'resume', 'close',
                     'resume_and_close'):
            with self.subTest(case=case):
                result = run_script('CASE = ' + repr(case) + '\n' + script, cli())
                self.assertEqual(result.returncode, 1, result.stderr)
                report = json.loads(result.stdout)
                self.assertEqual(report['failure_reason'],
                                 'cleanup_failed' if case == 'close' else 'containment_failed')
                self.assertEqual(report['secondary_failures'],
                                 ['cleanup_failed'] if case == 'resume_and_close' else [])
                self.assertIs(type(report['child_exit_code']), int)
                self.assertNotEqual(report['child_exit_code'], 0)
                self.assertEqual(report['child_stdout_base64'], '')
                self.assertEqual(report['applied_actions'], [])
                self.assertIsNone(report['settlement'])

    def test_partial_report_write_yields_nonzero_and_bounded_stderr_refusal(self):
        script = """
from unittest.mock import patch
real_write = h.os.write
def partial(fd, raw):
    return real_write(fd, raw[:13] if fd == 1 else raw)
with patch.object(h.os, 'write', partial):
    raise SystemExit(h.main(sys.argv[1:]))
"""
        result = run_script(script, cli())
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(len(result.stdout), 13)
        self.assertEqual(result.stderr, b'REFUSED output_failed\n')

    def test_job_configuration_failure_remains_first_when_close_also_fails(self):
        script = """
from unittest.mock import patch
api = h.ctypes.WinDLL('kernel32', use_last_error=True)
real_close = api.CloseHandle
real_close.argtypes = [h.ctypes.c_void_p]
real_close.restype = h.ctypes.c_int
def close_then_report_failure(handle):
    assert real_close(handle)
    return 0
with patch.object(h.ctypes, 'WinDLL', return_value=api), patch.object(
        api, 'SetInformationJobObject', return_value=0), patch.object(
        api, 'CloseHandle', side_effect=close_then_report_failure):
    raise SystemExit(h.main(sys.argv[1:]))
"""
        result = run_script(script, cli())
        report = json.loads(result.stdout)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(report['failure_reason'], 'containment_failed')
        self.assertEqual(report['secondary_failures'], ['cleanup_failed'])
        self.assertIsNone(report['child_exit_code'])
        self.assertEqual(report['applied_actions'], [])

    def test_failed_native_assignment_reaps_real_root_and_retains_its_exit(self):
        # Losing the partially constructed connection must not erase a real child receipt.
        script = """
from unittest.mock import patch
owned = []
real_popen = h.subprocess.Popen
def launch(*a, **kw):
    child = real_popen(*a, **kw)
    if '-c' in a[0]:
        owned.append(child)
    return child
real_assign = h.Job.assign
def refuse(self, child):
    with patch.object(self.api, 'AssignProcessToJobObject', return_value=0):
        return real_assign(self, child)
with patch.object(h.subprocess, 'Popen', launch), patch.object(h.Job, 'assign', refuse):
    code = h.main(sys.argv[1:])
assert len(owned) == 1 and owned[0].poll() is not None
assert owned[0].returncode != 0
raise SystemExit(code)
"""
        result = run_script(script, cli())
        self.assertEqual(result.returncode, 1, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report['failure_reason'], 'containment_failed')
        self.assertIs(type(report['child_exit_code']), int)
        self.assertNotEqual(report['child_exit_code'], 0)
        self.assertEqual(report['applied_actions'], [])
        self.assertIsNone(report['settlement'])


if __name__ == '__main__':
    unittest.main()
