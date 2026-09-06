"""Finite session resource controls; native ownership and cleanup remain real."""
from __future__ import annotations

import base64
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

REPO = Path(__file__).resolve().parents[1]
HARNESS = r'''
import _thread, ctypes, importlib.util, inspect, json, os, sys, tempfile, threading
from pathlib import Path
from unittest.mock import patch
spec = importlib.util.spec_from_file_location('session_boundary',
                                            Path.cwd() / 'tools/v0a_table_session.py')
t = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = t
spec.loader.exec_module(t)
api = ctypes.WinDLL('kernel32', use_last_error=True)
for name, args, result in (
    ('OpenProcess', [ctypes.c_ulong, ctypes.c_int, ctypes.c_ulong], ctypes.c_void_p),
    ('WaitForSingleObject', [ctypes.c_void_p, ctypes.c_ulong], ctypes.c_ulong),
    ('GetExitCodeProcess', [ctypes.c_void_p, ctypes.c_void_p], ctypes.c_int),
    ('IsProcessInJob', [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p], ctypes.c_int),
    ('QueryInformationJobObject', [ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p,
                                  ctypes.c_ulong, ctypes.c_void_p], ctypes.c_int),
    ('CloseHandle', [ctypes.c_void_p], ctypes.c_int),
):
    function = getattr(api, name)
    function.argtypes, function.restype = args, result

class Pids(ctypes.Structure):
    _fields_ = [('assigned', ctypes.c_ulong), ('count', ctypes.c_ulong),
                ('pids', ctypes.c_size_t * 64)]

connections, retained, violations, observed = [], {}, [], []
session = host = None
fired = False
workers = []
prompts = 0
output_calls = []

def retain(connection):
    if id(connection) in retained or connection.proc is None:
        return
    members = Pids()
    assert api.QueryInformationJobObject(connection.job.handle, 3,
        ctypes.byref(members), ctypes.sizeof(members), None), ctypes.get_last_error()
    assert 0 < members.count <= 64
    rows = []
    retained[id(connection)] = rows
    for pid in members.pids[:members.count]:
        handle = api.OpenProcess(0x100400, False, pid)
        assert handle, (pid, ctypes.get_last_error())
        rows.append((pid, handle))
        belongs = ctypes.c_int()
        assert api.IsProcessInJob(handle, connection.job.handle, ctypes.byref(belongs))
        assert belongs.value == 1
        assert api.WaitForSingleObject(handle, 0) == 258, 'member was not alive at retention'
    assert connection.proc.pid in [pid for pid, _ in rows]
    observed.append(['retained', len(rows)])

def stopped(boundary):
    # Observe without vetoing a bad next launch/prompt. Assertions happen after main.
    for rows in retained.values():
        for pid, handle in rows:
            value = api.WaitForSingleObject(handle, 0)
            if value != 0:
                violations.append([boundary, pid, value])

def asynchronous_interrupt(label):
    # A worker raises the main thread's pending interrupt while the real production
    # stack is at the declared cut. This changes timing only, never a native result.
    observed.append([label])
    def interrupt():
        _thread.interrupt_main()
    worker = threading.Thread(target=interrupt)
    workers.append(worker)
    worker.start()
    worker.join(5)
    raise AssertionError('scheduled interrupt was not delivered')

class Display:
    usable = True
    def heading(self, view, total):
        observed.append(['heading', view.ordinal])
    def update(self, view):
        global fired
        if not view.actions or fired:
            return
        if MODE in ('output', 'interrupt', 'output_then_interrupt', 'interrupt_then_cleanup'):
            fired = True
            observed.append(['action_trigger', view.ordinal, view.actions[0][0]])
            if MODE == 'interrupt_then_cleanup':
                connections[-1].job.close()
                observed.append(['actual_job_closed'])
            if MODE in ('interrupt', 'interrupt_then_cleanup'):
                raise KeyboardInterrupt()
            raise OSError('controlled renderer failure after applied action')
    def actions(self, rows, prefix=''):
        observed.append(['remaining', len(rows), prefix])
        if MODE == 'output_then_interrupt':
            stopped('later interrupt')
            observed.append(['later_observable_interrupt'])
            raise KeyboardInterrupt()
    def settled(self, payouts, stacks):
        stopped('settled publication')
        observed.append(['settled', list(stacks)])
    def prompt(self):
        global prompts
        prompts += 1
        stopped('prompt')
    def final(self, *args):
        pass

display = Display()
real_write = os.write
short_file = tempfile.TemporaryFile()
short_renderer = t.Renderer(short_file.fileno())

def partial(fd, raw):
    if fd == short_file.fileno():
        output_calls.append(raw.decode('ascii'))
        if raw.startswith(b'action '):
            observed.append(['partial_action_write'])
            return real_write(fd, raw[:7])
    return real_write(fd, raw)

def trace(frame, event, arg):
    global session, host, fired
    if frame.f_code is t.Session.prepare.__code__ and event == 'return':
        session = frame.f_locals['self']
        host = session.host
        if not MODE.startswith('constructor'):
            session.renderer = short_renderer if MODE == 'partial' else display
        session.command = lambda: b'n\n'
    if host is None:
        return trace
    if frame.f_code is host.ChildConnection.__init__.__code__:
        connection = frame.f_locals['self']
        if event == 'call':
            stopped('next constructor')
            connections.append(connection)
        if MODE.startswith('constructor') and event == 'line' and not fired:
            context = inspect.getframeinfo(frame).code_context
            if context == ['            self.job.resume(self.proc)\n']:
                retain(connection)
                if MODE == 'constructor_cleanup':
                    connection.job.close()
                    observed.append(['actual_job_closed'])
                fired = True
                asynchronous_interrupt('constructor_interrupt')
    if frame.f_code is host.WireConsumer.exchange.__code__:
        consumer = frame.f_locals['self']
        if event == 'call':
            retain(consumer.connection)
        if event == 'return' and consumer.table.applied_actions and not fired:
            if (MODE == 'late' and len(connections) == 2
                    and len(consumer.table.applied_actions) >= 6):
                fired = True
                observed.append(['late_exchange_failure', len(consumer.table.applied_actions)])
                raise host.HostRefusal('state_mismatch')
    if (MODE == 'cleanup' and host is not None and event == 'call'
            and frame.f_code is host.ChildConnection.finish.__code__ and not fired):
        # A real closed public Job is the specified non-interrupt cleanup fault.
        connection = frame.f_locals['self']
        assert frame.f_locals['success'] is True
        connection.job.close()
        fired = True
        observed.append(['actual_job_closed'])
    return trace

def profile(frame, event, arg):
    global fired
    if MODE != 'consumed' or fired or host is None:
        return
    if event == 'c_return' and getattr(arg, '__name__', '') == 'WaitForSingleObject':
        # The native process wait has actually run. Interrupt during its real Python
        # continuation, before finish accepts the exit; the Job/handles are still owned.
        cursor = frame
        while cursor is not None and cursor.f_code is not host.ChildConnection.finish.__code__:
            cursor = cursor.f_back
        if cursor is not None:
            connection = cursor.f_locals['self']
            assert cursor.f_locals['success'] is True and connection.job.handle
            assert connection is connections[-1] and retained[id(connection)]
            fired = True
            asynchronous_interrupt('interrupt_after_actual_native_wait')

args = ['--session', str(Path.cwd() / 'tests/fixtures/table_session/two_hands.json'),
        '--blueprint', str(Path.cwd() / 'tests/fixtures/table_host/empty_blueprint.json'),
        '--session-id', t.PREFIX + 'native-' + MODE, '--auto', '--format', 'json']
def transition_trace(frame, event, arg):
    trace(frame, event, arg)
    # Keep main's JSON receipt while exercising the real interactive transition.
    if MODE == 'between' and frame.f_code is t.Session.prepare.__code__ and event == 'return':
        session.args.auto = False
    return transition_trace

try:
    sys.settrace(transition_trace)
    sys.setprofile(profile)
    with patch.object(os, 'write', partial):
        code = t.main(args)
finally:
    sys.settrace(None)
    sys.setprofile(None)
    for worker in workers:
        worker.join(5)
        assert not worker.is_alive()
    stopped('main return')
    for connection in connections:
        root = next(handle for pid, handle in retained[id(connection)]
                    if pid == connection.proc.pid)
        native_exit = ctypes.c_ulong()
        if not api.GetExitCodeProcess(root, ctypes.byref(native_exit)):
            violations.append(['exit_query_failed', ctypes.get_last_error()])
        elif connection.exit_code != native_exit.value:
            violations.append(['exit_mismatch', connection.exit_code, native_exit.value])
    # Record outcome first; emergency cleanup cannot certify production termination.
    for connection in connections:
        if connection.proc is not None and connection.proc.poll() is None:
            connection.finish(False)
    for rows in retained.values():
        for _, handle in rows:
            assert api.CloseHandle(handle)
    short_file.seek(0)
    partial_bytes = short_file.read().decode('ascii')
    short_file.close()
assert not violations, violations
assert connections and all(c.proc is not None for c in connections)
assert len(retained) == len(connections)
assert all(c.closed and type(c.exit_code) is int for c in connections)
assert all(not worker.is_alive() for c in connections for worker in c.threads)
assert all(stream.closed for c in connections for stream in
           (c.proc.stdin, c.proc.stdout, c.proc.stderr))
if not MODE.startswith('constructor'):
    assert all(len(rows) >= 2 for rows in retained.values()), 'missing actual descendant control'
if MODE not in ('between', 'partial'):
    assert fired, 'failure schedule was not exercised'
if MODE == 'partial':
    assert sum(raw.startswith('action ') for raw in output_calls) == 1, output_calls
    assert partial_bytes.endswith('action '), partial_bytes
if MODE == 'between':
    assert prompts == 1 and len(connections) == 2
real_write(2, (json.dumps(dict(observed=observed, launches=len(connections), prompts=prompts,
                              output_calls=output_calls)) + '\n').encode())
raise SystemExit(code)
'''


class SessionNativeBoundaryTests(unittest.TestCase):
    def execute(self, mode, exit_code, reason=None):
        environment = {k: v for k, v in os.environ.items()
                       if not k.upper().startswith(('PYTHON', 'GIT_', 'PONTIUS_'))}
        environment['PONTIUS_GIT'] = os.environ['PONTIUS_GIT']
        result = subprocess.run([sys.executable, '-B', '-P', '-X',
            'int_max_str_digits=' + str(sys.get_int_max_str_digits()), '-c',
            'MODE = ' + repr(mode) + '\n' + HARNESS], cwd=REPO, env=environment,
            capture_output=True, timeout=120)
        self.assertEqual(result.returncode, exit_code, result.stderr.decode(errors='replace'))
        report = json.loads(result.stdout)
        observation = json.loads(result.stderr)
        self.assertEqual(report['failure_reason'], reason, report)
        self.assertEqual(observation['launches'], len(report['hands']))
        for entry in report['hands']:
            hand = entry['result']
            self.assertIs(type(hand['child_exit_code']), int)
            self.assertIs(hand['capture_truncated'], False)
            if not mode.startswith('constructor'):
                raw = base64.b64decode(hand['child_stdout_base64'], validate=True)
                self.assertIn(b'"ready"', raw)
                self.assertIn(b'"event_result"', raw)
        return report, observation

    def failed_first(self, mode, code, reason, secondary=()):
        report, observation = self.execute(mode, code, reason)
        self.assertEqual(report['status'], 'interrupted' if code == 130 else 'failed')
        self.assertEqual(report['secondary_failures'], list(secondary))
        self.assertEqual(report['completed_hands'], 0)
        self.assertEqual(report['carried_stacks'], [200] * 6)
        self.assertEqual(report['next_button'], 0)
        self.assertEqual(len(report['hands']), 1)
        hand = report['hands'][0]['result']
        self.assertEqual(hand['status'], 'failed')
        self.assertEqual(hand['failure_reason'], reason)
        self.assertEqual(hand['secondary_failures'], list(secondary))
        self.assertIsNone(hand['settlement'])
        actions = hand['applied_actions']
        self.assertTrue(actions)
        self.assertEqual(len(actions), 24 if mode in ('consumed', 'cleanup') else 1)
        self.assertEqual([a['index'] for a in actions], list(range(len(actions))))
        self.assertEqual(actions[0], dict(index=0, seat=3, street='preflop',
            action=dict(kind='call', raise_to=None), origin='bot'))
        self.assertFalse(any(row[0] == 'settled' for row in observation['observed']))
        self.assertEqual(observation['prompts'], 0)
        return report, observation

    def test_renderer_failure_after_real_action_terminates_root_and_descendant(self):
        self.failed_first('output', 1, 'output_failed')

    def test_observable_interrupt_retains_prefix_and_stops_before_next_launch(self):
        self.failed_first('interrupt', 130, 'interrupted')

    def test_output_failure_then_observable_interrupt_keeps_first_failure(self):
        self.failed_first('output_then_interrupt', 1, 'output_failed', ('interrupted',))

    def test_interrupt_then_real_closed_job_fault_preserves_cancel_status(self):
        self.failed_first('interrupt_then_cleanup', 130, 'interrupted', ('cleanup_failed',))

    def test_consumed_async_interrupt_inside_real_finish_is_cleanup_failure(self):
        _, observed = self.failed_first('consumed', 1, 'cleanup_failed')
        self.assertIn(['interrupt_after_actual_native_wait'], observed['observed'])

    def test_real_noninterrupt_cleanup_fault_cannot_publish_provisional_settlement(self):
        _, observed = self.failed_first('cleanup', 1, 'cleanup_failed')
        self.assertIn(['actual_job_closed'], observed['observed'])

    def test_late_second_hand_failure_preserves_first_settlement_and_active_prefix(self):
        report, observation = self.execute('late', 1, 'state_mismatch')
        self.assertEqual(report['status'], 'failed')
        self.assertEqual(report['completed_hands'], 1)
        self.assertEqual(report['carried_stacks'], [210, 198, 198, 198, 198, 198])
        self.assertEqual(report['next_button'], 1)
        self.assertEqual(len(report['hands']), 2)
        first, second = [entry['result'] for entry in report['hands']]
        self.assertEqual(first['status'], 'completed')
        self.assertEqual(first['settlement']['final_stacks'], report['carried_stacks'])
        self.assertEqual(first['child_exit_code'], 0)
        self.assertEqual(second['status'], 'failed')
        self.assertIsNone(second['settlement'])
        actions = second['applied_actions']
        self.assertTrue(actions)
        prefix = [row for row in observation['observed'] if row[0] == 'late_exchange_failure']
        self.assertEqual(prefix, [['late_exchange_failure', 6]])
        self.assertEqual(len(actions), 6)
        self.assertEqual([a['index'] for a in actions], list(range(len(actions))))
        self.assertEqual(actions[0], dict(index=0, seat=4, street='preflop',
            action=dict(kind='call', raise_to=None), origin='opponent'))
        self.assertEqual([row for row in observation['observed'] if row[0] == 'settled'],
                         [['settled', [210, 198, 198, 198, 198, 198]]])

    def test_real_native_members_have_terminated_before_prompt_and_second_launch(self):
        report, observation = self.execute('between', 0)
        self.assertEqual(report['status'], 'completed')
        self.assertEqual(report['completed_hands'], 2)
        self.assertEqual(report['carried_stacks'], [220, 196, 196, 196, 196, 196])
        self.assertEqual(observation['prompts'], 1)

    def test_constructor_consumed_interrupt_retains_host_phase_and_real_exit(self):
        report, observed = self.execute('constructor', 1, 'containment_failed')
        self.assertIn(['constructor_interrupt'], observed['observed'])
        self.assertEqual(report['status'], 'failed')
        self.assertEqual(report['completed_hands'], 0)
        self.assertEqual(len(report['hands']), 1)
        hand = report['hands'][0]['result']
        self.assertEqual(hand['failure_reason'], 'containment_failed')
        self.assertEqual(hand['applied_actions'], [])
        self.assertIsNone(hand['settlement'])
        self.assertNotEqual(hand['child_exit_code'], 0)
        self.assertNotIn('interrupted', report['secondary_failures'])

    def test_constructor_phase_then_real_cleanup_fault_keeps_both_inherited_reasons(self):
        report, observed = self.execute('constructor_cleanup', 1, 'containment_failed')
        self.assertIn(['constructor_interrupt'], observed['observed'])
        self.assertIn(['actual_job_closed'], observed['observed'])
        self.assertEqual(report['status'], 'failed')
        self.assertEqual(report['secondary_failures'], ['cleanup_failed'])
        self.assertEqual(report['completed_hands'], 0)
        self.assertEqual(report['carried_stacks'], [200] * 6)
        self.assertEqual(report['next_button'], 0)
        self.assertEqual(len(report['hands']), 1)
        hand = report['hands'][0]['result']
        self.assertEqual(hand['secondary_failures'], ['cleanup_failed'])
        self.assertEqual(hand['applied_actions'], [])
        self.assertIsNone(hand['settlement'])
        # Kill-on-close may report zero; the retained native root handle above is
        # the exit oracle. Cleanup success cannot be inferred from an exit code.
        self.assertIs(type(hand['child_exit_code']), int)

    def test_partial_real_action_publication_is_not_retried_after_cleanup(self):
        self.failed_first('partial', 1, 'output_failed')


if __name__ == '__main__':
    unittest.main()
