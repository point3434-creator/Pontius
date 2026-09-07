"""Finite session behavior with independently calculated hands; no operating population."""
from __future__ import annotations
import base64
import json
import os
from pathlib import Path
import queue
import subprocess
import sys
import threading
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[1]
TOOL = REPO / 'tools/v0a_table_session.py'
FIXTURES = REPO / 'tests/fixtures/table_session'
BLUEPRINT = REPO / 'tests/fixtures/table_host/empty_blueprint.json'
PREFIX = 'pontius-v0a-table-session-v1-correctness-'
LOAD = """
import importlib.util, json, sys
from pathlib import Path
spec = importlib.util.spec_from_file_location('session_under_test',
    Path.cwd() / 'tools/v0a_table_session.py')
m = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = m
spec.loader.exec_module(m)
"""


def cli(path=None):
    return ['--session', str(path or FIXTURES / 'two_hands.json'), '--blueprint',
            str(BLUEPRINT), '--session-id', PREFIX + 'controls', '--auto', '--format', 'json']


def run_script(script, args=None, cwd=REPO):
    return subprocess.run([sys.executable, '-B', '-P', '-X',
        'int_max_str_digits=' + str(sys.get_int_max_str_digits()), '-c', LOAD + script,
        *(cli() if args is None else args)], cwd=cwd, env=os.environ.copy(),
        capture_output=True, timeout=150)


def invoke(name='two_hands', *, extra=(), commands=b''):
    environment = {k: v for k, v in os.environ.items()
                   if not k.upper().startswith(('PYTHON', 'GIT_'))}
    return subprocess.run([sys.executable, '-B', '-P', str(TOOL), '--session',
        str(FIXTURES / (name + '.json')), '--blueprint', str(BLUEPRINT),
        '--session-id', PREFIX + name, *extra], input=commands, cwd=REPO,
        env=environment, capture_output=True, timeout=150)


class RealSessionTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(TOOL.is_file(), 'approved multi-hand session tool is absent')

    def test_two_real_hands_carry_settled_stacks_rotate_button_and_keep_unique_ids(self):
        # Reset stacks, stationary button, skipped/doubled actions or synthetic hands fail.
        process = invoke(extra=('--auto', '--format', 'json'))
        self.assertEqual(process.returncode, 0, (process.stdout, process.stderr))
        report = json.loads(process.stdout)
        self.assertEqual(report['status'], 'completed')
        self.assertIsNone(report['failure_reason'])
        self.assertIsNone(report['stop_reason'])
        self.assertEqual(report['secondary_failures'], [])
        self.assertEqual(report['completed_hands'], 2)
        self.assertEqual(report['carried_stacks'], [220, 196, 196, 196, 196, 196])
        self.assertEqual(report['next_button'], 2)
        self.assertEqual([r['button'] for r in report['hands']], [0, 1])
        self.assertEqual([r['starting_stacks'] for r in report['hands']],
                         [[200] * 6, [210, 198, 198, 198, 198, 198]])
        expected = [
            [(3, 'call'), (4, 'call'), (5, 'call'), (0, 'call'), (1, 'call'), (2, 'check')]
            + [(s, 'check') for s in (1, 2, 3, 4, 5, 0)] * 3,
            [(4, 'call'), (5, 'call'), (0, 'call'), (1, 'call'), (2, 'call'), (3, 'check')]
            + [(s, 'check') for s in (2, 3, 4, 5, 0, 1)] * 3,
        ]
        ids = []
        for ordinal, (entry, actions) in enumerate(zip(report['hands'], expected), 1):
            hand = entry['result']
            self.assertEqual(entry['ordinal'], ordinal)
            self.assertEqual(hand['status'], 'completed')
            self.assertEqual(hand['child_exit_code'], 0)
            self.assertIs(hand['capture_truncated'], False)
            self.assertEqual(hand['secondary_failures'], [])
            self.assertEqual(hand['settlement']['payouts'], [12, 0, 0, 0, 0, 0])
            self.assertEqual(sum(hand['settlement']['final_stacks']), 1200)
            rows = hand['applied_actions']
            self.assertEqual([(r['seat'], r['action']['kind']) for r in rows], actions)
            self.assertEqual([r['index'] for r in rows], list(range(24)))
            self.assertEqual([r['street'] for r in rows],
                             ['preflop'] * 6 + ['flop'] * 6 + ['turn'] * 6 + ['river'] * 6)
            self.assertTrue(all(r['action']['raise_to'] is None for r in rows))
            self.assertTrue(all(r['origin'] == ('bot' if r['seat'] == 3 else 'opponent')
                                for r in rows))
            wire = [json.loads(line) for line in
                    base64.b64decode(hand['child_stdout_base64']).splitlines()]
            self.assertTrue(wire)
            child_id = 'pontius-v0a-event-interface-v1-correctness-table-two_hands-h%02d' % ordinal
            self.assertTrue(all(r['session_id'] == child_id for r in wire))
            ids.append(child_id)
        self.assertEqual(len(set(ids)), 2)

    def test_below_blind_stacks_stop_after_one_complete_sidepot_hand(self):
        # Running another child or resetting/eliminating zero-stack seats fails this control.
        process = invoke('below_blind', extra=('--auto', '--format', 'json'))
        self.assertEqual(process.returncode, 0, (process.stdout, process.stderr))
        report = json.loads(process.stdout)
        self.assertEqual((report['status'], report['stop_reason']),
                         ('stopped', 'insufficient_stacks'))
        self.assertEqual(report['completed_hands'], 1)
        self.assertEqual(len(report['hands']), 1)
        self.assertEqual(report['carried_stacks'], [24, 20, 16, 0, 0, 0])
        self.assertEqual(report['next_button'], 1)
        hand = report['hands'][0]['result']
        self.assertEqual(hand['child_exit_code'], 0)
        self.assertEqual([p['amount'] for p in hand['settlement']['pots']], [24, 20, 16])

    def test_text_auto_shows_actual_actions_and_only_bot_cards(self):
        # Printing a final JSON dump or a dealer's hole cards fails the visible interface.
        process = invoke(extra=('--auto',))
        self.assertEqual(process.returncode, 0, process.stderr)
        text = process.stdout.decode('ascii')
        self.assertIn('Hand 1/2', text)
        self.assertIn('Hand 2/2', text)
        self.assertIn('Jc Jd', text)
        self.assertIn('flop', text)
        self.assertIn('2c 3d 4h', text)
        self.assertIn('action 0 seat 3 preflop call', text)
        self.assertIn('220 196 196 196 196 196', text)
        self.assertNotIn('Ac', text)
        self.assertNotIn('Ad', text)
        self.assertNotIn('Kc', text)
        self.assertNotIn('child_stdout_base64', text)
        self.assertNotIn('Next', text)

    def test_interactive_next_quit_eof_and_invalid_commands_control_real_hands(self):
        # Ignoring input, accepting partial commands or launching before permission fails.
        for command, hands, code, reason in (
            (b'\n', 2, 0, 'completed'), (b'n\r\n', 2, 0, 'completed'),
            (b'q\n', 1, 0, 'quit'), (b'', 1, 0, 'eof'),
            (b'next\n', 1, 1, 'command_invalid'), (b'n', 1, 1, 'command_invalid'),
            (b'qqqqqqqqq\n', 1, 1, 'command_invalid'),
        ):
            with self.subTest(command=command):
                process = invoke(commands=command)
                self.assertEqual(process.returncode, code, (process.stdout, process.stderr))
                text = process.stdout.decode()
                self.assertEqual(text.count('Hand '), hands)
                self.assertIn(reason, text)

    def test_text_arrives_while_the_session_is_waiting_for_the_next_command(self):
        # Buffering until EOF or launching hand two before the user's command fails.
        process = subprocess.Popen([sys.executable, '-B', '-P', str(TOOL), '--session',
            str(FIXTURES / 'two_hands.json'), '--blueprint', str(BLUEPRINT),
            '--session-id', PREFIX + 'live'], cwd=REPO, stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        lines = queue.Queue()
        reader = threading.Thread(target=lambda: [lines.put(line) for line in process.stdout],
                                  daemon=True)
        reader.start()
        seen = []
        try:
            while not seen or not seen[-1].startswith(b'Next'):
                seen.append(lines.get(timeout=45))
            self.assertTrue(seen[0].startswith(b'Hand 1/2'))
            self.assertTrue(any(b'action 0 seat 3' in line for line in seen))
            self.assertFalse(any(b'Hand 2/' in line for line in seen))
            process.stdin.write(b'q\n')
            process.stdin.close()
            self.assertEqual(process.wait(timeout=30), 0)
            reader.join(timeout=5)
            self.assertFalse(reader.is_alive())
        finally:
            if process.poll() is None:
                process.kill()
                process.wait(timeout=10)
            for stream in (process.stdin, process.stdout, process.stderr):
                stream.close()


class InputAndProjectionTests(unittest.TestCase):
    def test_schedule_rejects_exact_type_card_depth_number_and_member_faults(self):
        # A lax decoder must not admit impossible deals or bool-valued stack/button fields.
        result = run_script("""
s = m.Session(m.arguments(sys.argv[1:])); s.prepare()
good = json.loads(s.session_input.raw)
cases = []
for key, value in [('button', True), ('controlled_seat', 6), ('starting_stacks', [1]*6),
                   ('starting_stacks', [True]*6), ('starting_stacks', None),
                   ('starting_stacks', 200), ('big_blind', 1), ('small_blind', 0),
                   ('hands', []), ('hands', good['hands']*9), ('hands', {}),
                   ('opponents', ['passive']*6), ('version', 'wrong')]:
    changed = dict(good); changed[key] = value; cases.append(m.encode(changed))
for key, value in [('private_hands', [[0,0]]*6), ('board_runout', [0,1,2,3,True]),
                   ('board_runout', [0,1,2,3,52]), ('extra', 1)]:
    changed = json.loads(s.session_input.raw)
    changed['hands'][1][key] = value; cases.append(m.encode(changed))
cases += [b'\\xef\\xbb\\xbf{}', b'{}\\r\\n', b'{"x":1,"x":2}', b'{"x":1.0}',
          b'{"x":NaN}', b'{"x":"\\xff"}', b'['*9+b']'*9,
          b'{"x":'+b'9'*641+b'}', b'{"x":12345678}', b' '*16385]
for raw in cases:
    try:
        m.Schedule(raw, s.host, s.modules)
    except (m.Refusal, s.host.HostRefusal) as error:
        assert error.code == 'input_invalid', (raw[:80], error)
    else:
        raise AssertionError(('accepted invalid input', raw[:80]))
print(len(cases))
""")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), b'27')

    def test_malformed_schedule_and_blueprint_report_input_failure_before_any_hand(self):
        # Preparation must classify input faults as input_invalid, not source failure.
        for target in ('session', 'blueprint'):
            with self.subTest(target=target), tempfile.TemporaryDirectory() as directory:
                bad = Path(directory) / 'bad.json'
                bad.write_bytes(b'{}\n')
                args = cli()
                args[args.index('--' + target) + 1] = str(bad)
                result = run_script('raise SystemExit(m.main(sys.argv[1:]))', args)
                self.assertEqual(result.returncode, 1, result.stderr)
                report = json.loads(result.stdout)
                self.assertEqual(report['failure_reason'], 'input_invalid')
                self.assertEqual(report['hands'], [])
                self.assertEqual(report['completed_hands'], 0)

    def test_projection_is_immutable_and_has_only_current_public_and_own_cards(self):
        # Accidentally handing the renderer a Table/deal or nested mutable containers fails.
        result = run_script("""
import dataclasses
s = m.Session(m.arguments(sys.argv[1:])); s.prepare()
config, _ = s.schedule.derive(0, [200]*6, 0)
table = s.host.Table(config, s.modules, 'declared-projection')
view = m.visible(table, 1, 0)
assert view.cards == ('Jc','Jd') and view.board == ()
assert view.actions == () and view.stacks == (200,199,198,200,200,200)
def primitive(value):
    return type(value) in (int,str,type(None)) or type(value) is tuple and all(map(primitive,value))
assert all(primitive(getattr(view,f.name)) for f in dataclasses.fields(view))
try:
    view.bot = 4
except dataclasses.FrozenInstanceError:
    pass
else:
    raise AssertionError('mutable visible state')
print('visible-only')
""")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), b'visible-only')

    def test_hidden_pairs_and_future_deals_do_not_change_earlier_cli_output(self):
        # A renderer reading the full dealer schedule leaks information before it is public.
        original = json.loads((FIXTURES / 'two_hands.json').read_bytes())
        baseline = invoke(commands=b'q\n').stdout
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'hidden-permutation.json'
            changed = json.loads(json.dumps(original))
            for deal in changed['hands']:
                deal['private_hands'][1], deal['private_hands'][2] = (
                    deal['private_hands'][2], deal['private_hands'][1])
            changed['hands'][1]['board_runout'].reverse()
            path.write_bytes(json.dumps(changed).encode())
            args = cli(path)[:-3]  # Remove --auto --format json; text interactive remains.
            result = subprocess.run([sys.executable, '-B', '-P', str(TOOL), *args],
                input=b'q\n', cwd=REPO, capture_output=True, timeout=90)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, baseline)

    def test_auto_and_interactive_routes_return_same_game_results(self):
        # A separate interactive state machine would risk divergent carryover or actions.
        result = run_script("""
args = m.arguments(sys.argv[1:]); args.auto = False
s = m.Session(args, command=lambda: b'n\\n')
print(json.dumps(s.run()))
""")
        self.assertEqual(result.returncode, 0, result.stderr)
        auto = json.loads(invoke(extra=('--auto', '--format', 'json')).stdout)
        interactive = json.loads(result.stdout)
        for key in ('status', 'completed_hands', 'carried_stacks', 'next_button'):
            self.assertEqual(interactive[key], auto[key])
        for left, right in zip(interactive['hands'], auto['hands']):
            for key in ('starting_stacks', 'button', 'ordinal'):
                self.assertEqual(left[key], right[key])
            for key in ('applied_actions', 'settlement', 'status', 'child_exit_code'):
                self.assertEqual(left['result'][key], right['result'][key])

    def test_schedule_and_blueprint_drift_after_prompt_stop_before_second_hand(self):
        # Reusing cached admission after a user's pause would run a changed owned input.
        for target in ('session_input', 'blueprint_input'):
            with self.subTest(target=target), tempfile.TemporaryDirectory() as directory:
                schedule, blueprint = Path(directory) / 'schedule.json', Path(directory) / 'bp.json'
                schedule.write_bytes((FIXTURES / 'two_hands.json').read_bytes())
                blueprint.write_bytes(BLUEPRINT.read_bytes())
                args = cli(schedule)
                args[args.index('--blueprint') + 1] = str(blueprint)
                result = run_script("""
args = m.arguments(sys.argv[1:]); args.auto = False
s = m.Session(args)
def command():
    path = getattr(s, TARGET).path
    path.write_bytes(path.read_bytes()+b' ')
    return b'n\\n'
s.command = command
print(json.dumps(s.run()))
""".replace('TARGET', repr(target)), args)
                self.assertEqual(result.returncode, 0, result.stderr)
                report = json.loads(result.stdout)
                self.assertEqual(report['status'], 'failed')
                self.assertEqual(report['failure_reason'], 'input_invalid')
                self.assertEqual(report['completed_hands'], 1)
                self.assertEqual(len(report['hands']), 1)
                self.assertEqual(report['carried_stacks'], [210, 198, 198, 198, 198, 198])

    def test_help_and_argument_errors_do_not_import_host_or_start_a_child(self):
        # Argument processing should work even when source admission would refuse.
        result = run_script("""
import types
sys.modules['pontius'] = types.ModuleType('pontius')
raise SystemExit(m.main(['--help']))
""")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(b'--session', result.stdout)
        result = run_script('raise SystemExit(m.main(sys.argv[1:]))',
                            cli()[:-3] + ['--format','json'])
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, b'')

    def test_source_and_preloaded_module_refusals_precede_all_hands(self):
        # Cache/import contamination cannot bypass the admission gate.
        for name in ('pontius', 'pontius.fake', 'pontius_v0a_table_session_host'):
            result = run_script("""
import types
sys.modules[NAME] = types.ModuleType(NAME)
raise SystemExit(m.main(sys.argv[1:]))
""".replace('NAME', repr(name)))
            self.assertEqual(result.returncode, 1, result.stderr)
            report = json.loads(result.stdout)
            self.assertEqual(report['failure_reason'], 'source_invalid')
            self.assertEqual(report['hands'], [])


class SourceAndOutputTests(unittest.TestCase):
    def test_final_json_short_write_reports_failure_without_retry(self):
        # A successful game cannot turn a partially published JSON summary into success.
        result = run_script("""
real_write, writes = m.os.write, []
def short(fd, raw):
    if fd == 1:
        writes.append(len(raw)); return real_write(fd, raw[:7])
    return real_write(fd, raw)
m.os.write = short
code = m.main(sys.argv[1:])
assert code == 1 and len(writes) == 1 and writes[0] > 7
raise SystemExit(code)
""")
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(len(result.stdout), 7)
        self.assertEqual(result.stderr, b'REFUSED output_failed\n')

    def test_command_read_failure_and_interrupt_preserve_accepted_hand(self):
        # A prompt failure follows the accepted settlement and cannot create another hand.
        for error, reason, status in (('OSError()', 'input_failed', 'failed'),
                                       ('KeyboardInterrupt()', 'interrupted', 'interrupted')):
            result = run_script("""
args = m.arguments(sys.argv[1:]); args.auto = False
def command():
    raise ERROR
print(json.dumps(m.Session(args, command=command).run()))
""".replace('ERROR', error))
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(result.stdout)
            self.assertEqual((report['failure_reason'], report['status']), (reason, status))
            self.assertEqual(report['completed_hands'], 1)
            self.assertEqual(len(report['hands']), 1)
            self.assertEqual(report['hands'][0]['result']['status'], 'completed')
            self.assertEqual(report['carried_stacks'], [210,198,198,198,198,198])

    def clone(self, destination):
        # Only disposable test-owned clones change; no sealed checkout is edited.
        git = os.environ['PONTIUS_GIT']
        result = subprocess.run([git, '-c', 'core.autocrlf=false', 'clone', '--quiet',
            '--no-hardlinks', str(REPO), str(destination)], capture_output=True, timeout=60)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_raw_self_and_host_mismatch_refuse_before_module_execution(self):
        # Raw bytes, including a changed host committed under a new blob, must stay pinned.
        for target, committed in (('v0a_table_session.py', False), ('v0a_table_host.py', False),
                                  ('v0a_table_host.py', True)):
            with self.subTest(target=target, committed=committed):
                with tempfile.TemporaryDirectory() as directory:
                    clone = Path(directory) / 'clone'
                    self.clone(clone)
                    path = clone / 'tools' / target
                    path.write_bytes(path.read_bytes() + b'\n# deliberate source drift\n')
                    if committed:
                        git = os.environ['PONTIUS_GIT']
                        for command in (['add', '--', 'tools/' + target],
                            ['-c','user.name=Test','-c','user.email=test@localhost',
                             '-c','core.hooksPath=' + str(clone / 'absent-hooks'),
                             'commit','--quiet','-m','Test-owned changed-host control']):
                            result = subprocess.run([git, '-C', str(clone), *command],
                                capture_output=True, timeout=30)
                            self.assertEqual(result.returncode, 0, result.stderr)
                    result = run_script("""
s = m.Session(m.arguments(sys.argv[1:]))
report = s.run()
assert m.ALIAS not in sys.modules
print(json.dumps(report))
""", cwd=clone)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    report = json.loads(result.stdout)
                    self.assertEqual(report['failure_reason'], 'source_invalid')
                    self.assertEqual(report['hands'], [])

    def test_source_drift_after_prompt_is_checked_on_next_and_quit(self):
        # Both the next launch and final publication must recheck owned source bytes.
        for command in ('n', 'q'):
            with self.subTest(command=command), tempfile.TemporaryDirectory() as directory:
                clone = Path(directory) / 'clone'
                self.clone(clone)
                result = run_script("""
args = m.arguments(sys.argv[1:]); args.auto = False
def command():
    path = Path.cwd() / m.SELF
    path.write_bytes(path.read_bytes()+b'\\n# prompt drift\\n')
    return COMMAND
s = m.Session(args, command=command)
print(json.dumps(s.run()))
""".replace('COMMAND', repr((command + '\n').encode())), cwd=clone)
                self.assertEqual(result.returncode, 0, result.stderr)
                report = json.loads(result.stdout)
                self.assertEqual(report['failure_reason'], 'source_invalid')
                self.assertEqual(report['completed_hands'], 1)
                self.assertEqual(len(report['hands']), 1)
                self.assertEqual(report['hands'][0]['result']['status'], 'completed')
                self.assertEqual(report['carried_stacks'], [210,198,198,198,198,198])

    def test_renderer_caps_refuse_without_writing_and_short_write_is_never_retried(self):
        # The public renderer must stop after a short actual write, and bound line/session size.
        result = run_script("""
import tempfile
with tempfile.TemporaryFile() as stream:
    for text, total in [('x'*4096, 0), ('ok', 4194304)]:
        renderer = m.Renderer(stream.fileno()); renderer.written = total
        try:
            renderer.line(text)
        except m.Refusal as error:
            assert error.code == 'output_failed'
        else:
            raise AssertionError('output cap bypass')
        assert stream.tell() == 0 and not renderer.usable
    real_write, calls = m.os.write, []
    def short(fd, raw):
        calls.append(bytes(raw)); return real_write(fd, raw[:2])
    m.os.write = short
    renderer = m.Renderer(stream.fileno())
    for text in ('abcdef', 'later'):
        try:
            renderer.line(text)
        except m.Refusal as error:
            assert error.code == 'output_failed'
        else:
            raise AssertionError('short write ignored')
    assert calls == [b'abcdef\\n']
    stream.seek(0); assert stream.read() == b'ab'
print('bounded-one-shot')
""")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), b'bounded-one-shot')


class RegistrationPolicyTests(unittest.TestCase):
    def test_real_boundary_policy_rejects_extra_imports_and_changed_fixed_host(self):
        # The new tool must not inherit a generic sibling-tool or standard-library allowance.
        import importlib.util
        spec = importlib.util.spec_from_file_location('session_boundary_checker',
            REPO / 'tools/check_stabilization_boundaries.py')
        checker = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(checker)
        self.assertTrue(hasattr(checker, 'enforce_table_session_import_policy'),
                        'the bounded session import policy is absent')
        raw = TOOL.read_bytes()
        key = 'tools/v0a_table_session.py'
        checker.enforce_table_session_import_policy({key: raw})
        self.assertEqual(raw.count(b'7beb178989b3ff98b684093ce4022667a1c61ece'), 1)
        for changed in (raw + b'\nimport signal\n', raw + b'\nimport pontius.v0a.runtime\n',
                        raw + b'\nimport tools.v0a_event_adapter\n',
                        raw.replace(b'tools/v0a_table_host.py', b'tools/v0a_event_adapter.py'),
                        raw.replace(b'7beb178989b3ff98b684093ce4022667a1c61ece', b'0'*40)):
            with self.assertRaises(checker.BoundaryError):
                checker.enforce_table_session_import_policy({key: changed})


if __name__ == '__main__':
    unittest.main()
