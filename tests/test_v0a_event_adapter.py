"""Declared event-interface correctness cases; no operating population."""
from __future__ import annotations
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[1]
TOOL = REPO / 'tools/v0a_event_adapter.py'
FIXTURES = REPO / 'tests/fixtures/event_adapter'
PREFIX = 'pontius-v0a-event-interface-v1-correctness-'
SESSION = PREFIX + 'declared'
COMMON = {'protocol', 'session_id', 'type'}
FIELDS = {
    'ready': {'source_commit', 'source_manifest_sha256', 'blueprint_artifact_sha256',
              'blueprint_sha256', 'evidentiary'},
    'action': {'hand_id', 'action_index', 'seat', 'street', 'action'},
    'event_result': {'event_index', 'status', 'decision', 'failure'},
    'hand_result': {'complete', 'settlement', 'rank_source', 'evidentiary',
                    'preparation_compute_seconds', 'post_terminal_compute_seconds',
                    'interrupted_response_count', 'accounting_complete', 'failure_reason',
                    'secondary_failures'},
    'session_result': {'status', 'terminal_publication_compute_seconds', 'accounting_complete',
                       'failure_reason', 'secondary_failures', 'accounting_scope', 'evidentiary'},
}

# Test-only schedules at the real clock, decoder and write boundaries. Every
# native byte count, runtime transition, public interval and finalizer stays real.
HOST_SCHEDULE = '''
class Tick:
    ns, bad = 1000000000, False
    def __call__(self):
        self.ns += 1000000
        return None if self.bad else self.ns
tick = Tick()
load = m.Source.load
def loaded(self):
    modules = load(self)
    core, clock = modules[2:4]
    clock.time.monotonic_ns = tick
    publication = core.HandRuntime.owned_publication
    def publish(self, *args, **kwargs):
        if mode == 'entry':
            tick.bad = True
        return publication(self, *args, **kwargs)
    core.HandRuntime.owned_publication = publish
    finalize = core.HandRuntime.finalize_accounting
    def finish(self):
        if mode == 'finalizer':
            tick.bad = True
        return finalize(self)
    core.HandRuntime.finalize_accounting = finish
    check = m.Source.check
    def recheck(self):
        check(self)
        if mode == 'source_and_close':
            raise ValueError('declared source failure')
    m.Source.check = recheck
    return modules
m.Source.load = loaded
native = os.write
def write(fd, raw):
    kind = json.loads(raw)['type'] if fd == sys.stdout.fileno() else None
    if kind == 'hand_result' and mode in ('body', 'body_and_close'):
        try:
            return native(-1, raw)
        finally:
            tick.bad = mode == 'body_and_close'
    if kind == 'session_result' and mode in ('last_short', 'last_failed'):
        return native(fd if mode == 'last_short' else -1, raw[:11])
    count = native(fd, raw)
    if kind == 'action' and mode == 'duplicate':
        native(fd, raw)
    if kind == 'hand_result' and mode in ('closing', 'source_and_close'):
        tick.bad = True
    return count
os.write = write
frame = m.PipeOutput.frame
def altered(self, kind, **fields):
    if kind == 'hand_result':
        if mode == 'zero_cost':
            fields['preparation_compute_seconds'] = 0.0
        if mode == 'omit_cost':
            del fields['post_terminal_compute_seconds']
        if mode == 'wrong_bool':
            fields['complete'] = 1
    return frame(self, kind, **fields)
m.PipeOutput.frame = altered
if mode == 'false_exit':
    m.refuse = lambda reason: 0
if mode == 'late_start':
    factory, decode = m.runtime_type, m.decode_frame
    def delayed(*args):
        tick.ns += 2000000000
        return decode(*args)
    m.decode_frame = delayed
    def late(*args):
        cls = factory(*args)
        def dispatch(self, raw):
            value = m.decode_frame(raw, self.session_id, args[0])
            self.event_index = value.event_index
            return self.dispatch(value)
        cls.dispatch_frame = dispatch
        return cls
    m.runtime_type = late
'''


def wire(value):
    return (json.dumps(value, separators=(',', ':'), allow_nan=False) + '\n').encode()


def event(kind='hand_started', index=0, **values):
    result = dict(kind=kind, schema_version='pontius-v0a-event-v1', hand_id=SESSION,
                  event_index=index)
    if kind == 'hand_started':
        result.update(button=0, controlled_seat=3, starting_stacks=[200] * 6,
                      small_blind=1, big_blind=2, private_cards=[48, 49])
    result.update(values)
    return result


def opponent(index, seat, kind='fold', street='preflop', raise_to=None):
    return event('opponent_action', index, seat=seat, street=street,
                 action=dict(kind=kind, raise_to=raise_to))


def load_tool():
    spec = importlib.util.spec_from_file_location('event_adapter_under_test', TOOL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Consumer:
    """Independent frame/identity oracle; diagnostics never instruct an action."""
    def __init__(self, case, process):
        self.case, self.process, self.actions, self.rows = case, process, set(), []

    def read(self):
        raw = self.process.stdout.readline()
        self.case.assertTrue(raw.endswith(b'\n'), raw)
        self.case.assertNotIn(b'\r', raw)
        row = json.loads(raw)
        self.case.assertEqual(raw, wire(dict(sorted(row.items()))))
        self.case.assertEqual(set(row), COMMON | FIELDS[row['type']])
        self.case.assertEqual(row['protocol'], 'pontius-v0a-event-interface-v1')
        self.case.assertEqual(row['session_id'], SESSION)
        if (row['type'] == 'event_result' and row['decision']
                and getattr(self, 'minimum_elapsed', 0)):
            elapsed = row['decision']['timing']['elapsed_ns']
            self.case.assertGreaterEqual(elapsed, self.minimum_elapsed)
        for key in ('complete', 'accounting_complete', 'evidentiary'):
            if key in row:
                self.case.assertIs(type(row[key]), bool)
        for key in ('event_index', 'action_index', 'seat', 'interrupted_response_count'):
            if key in row and (key != 'event_index' or row[key] is not None):
                self.case.assertIs(type(row[key]), int)
                self.case.assertGreaterEqual(row[key], 0)
        if 'status' in row:
            self.case.assertIn(row['status'], ('accepted', 'decided', 'failed', 'completed'))
        if 'rank_source' in row:
            self.case.assertIn(row['rank_source'], (None, 'host_supplied', 'not_required'))
        for key in ('preparation_compute_seconds', 'post_terminal_compute_seconds',
                    'terminal_publication_compute_seconds'):
            if key in row and row[key] is not None:
                self.case.assertIs(type(row[key]), float)
                self.case.assertTrue(0 <= row[key] < float('inf'))
        for key in ('decision', 'failure', 'settlement'):
            if key in row and row[key] is not None:
                self.case.assertIs(type(row[key]), dict)
        if 'secondary_failures' in row:
            self.case.assertIs(type(row['secondary_failures']), list)
            for value in [row['failure_reason'], *row['secondary_failures']]:
                self.case.assertTrue(value is None or type(value) is str)
        if row['type'] == 'action':
            self.case.assertEqual(set(row['action']), {'kind', 'raise_to'})
            self.case.assertIn(row['action']['kind'], ('fold', 'check', 'call', 'raise'))
            if row['action']['raise_to'] is not None:
                self.case.assertIs(type(row['action']['raise_to']), int)
            self.case.assertIs(type(row['hand_id']), str)
            self.case.assertIs(type(row['street']), str)
            identity = row['hand_id'], row['action_index']
            self.case.assertNotIn(identity, self.actions)
            self.actions.add(identity)
        self.rows.append(row)
        return row

    def send(self, value):
        self.process.stdin.write(wire(value))
        self.process.stdin.flush()
        rows = [self.read()]
        if rows[0]['type'] == 'action':
            rows.append(self.read())
        self.case.assertEqual(rows[-1]['type'], 'event_result')
        return rows

    def completed(self, *, positive=False):
        hand, session = self.read(), self.read()
        self.case.assertEqual((hand['type'], session['type']), ('hand_result', 'session_result'))
        self.case.assertIs(hand['complete'], True)
        self.case.assertEqual(session['status'], 'completed')
        for row in (hand, session):
            self.case.assertIs(row['accounting_complete'], True)
            self.case.assertIs(row['evidentiary'], False)
            self.case.assertIsNone(row['failure_reason'])
            self.case.assertEqual(row['secondary_failures'], [])
        for value in (hand['preparation_compute_seconds'], hand['post_terminal_compute_seconds'],
                      session['terminal_publication_compute_seconds']):
            self.case.assertIs(type(value), float)
            self.case.assertGreaterEqual(value, 0)
            self.case.assertLess(value, float('inf'))
            if positive:
                self.case.assertGreater(value, 0, (hand, session))
        self.case.assertEqual(session['accounting_scope'], 'runtime_begin_to_final_publication')
        self.case.assertEqual(self.process.stdout.read(), b'')
        self.case.assertEqual(self.process.wait(timeout=15), 0)
        self.case.assertEqual(self.process.stderr.read(), b'')
        return hand


class EventPipeTests(unittest.TestCase):
    def instrument(self, body):
        return ("import importlib.util,sys,os,json,time\n"
                "s=importlib.util.spec_from_file_location('adapter','tools/v0a_event_adapter.py')\n"
                "m=importlib.util.module_from_spec(s);s.loader.exec_module(m)\n" + body +
                "\nraise SystemExit(m.main())\n")

    def start(self, name='fold', policy=None, code=None):
        self.assertTrue(TOOL.is_file(), 'The approved event CLI is not implemented')
        directory = Path(tempfile.mkdtemp(prefix='event-policy-', dir=REPO.parent))
        path = directory / 'blueprint.json'
        path.write_bytes(policy if policy is not None else
                         (FIXTURES / f'{name}_blueprint.json').read_bytes())
        child = {k: v for k, v in os.environ.items()
                 if not k.upper().startswith(('GIT_', 'PYTHON', 'PONTIUS_'))}
        child.update(PYTHONPATH=str(REPO / 'src'), PONTIUS_GIT=os.environ['PONTIUS_GIT'])
        command = ['-c', code] if code is not None else [str(TOOL)]
        process = subprocess.Popen([sys.executable, '-B', '-P', '-X',
                                    f'int_max_str_digits={sys.get_int_max_str_digits()}',
                                    *command, '--blueprint', str(path),
                                    '--session-id', SESSION], cwd=REPO, env=child,
                                   stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        timer = threading.Timer(60, process.kill)
        timer.start()
        def close():
            if process.poll() is None:
                process.kill()
            process.wait(timeout=15)
            for stream in (process.stdin, process.stdout, process.stderr):
                stream.close()
            timer.cancel()
        self.addCleanup(close)
        consumer = Consumer(self, process)
        ready = consumer.read()
        self.assertEqual(ready['type'], 'ready')
        self.assertIs(ready['evidentiary'], False)
        self.assertRegex(ready['source_commit'], '^[0-9a-f]{40}$')
        for key in ('source_manifest_sha256', 'blueprint_artifact_sha256', 'blueprint_sha256'):
            self.assertRegex(ready[key], '^[0-9a-f]{64}$')
        self.assertEqual(ready['blueprint_artifact_sha256'],
                         hashlib.sha256(path.read_bytes()).hexdigest())
        return consumer

    def test_real_caller_waits_for_raise_before_choosing_folds(self):
        consumer = self.start()
        action, result = consumer.send(event())
        self.assertEqual(action['action'], {'kind': 'raise', 'raise_to': 8})
        self.assertEqual(result['decision']['selection_reason'], 'table_hit')
        for index, seat in enumerate((4, 5, 0, 1, 2), 1):
            self.assertEqual(consumer.send(opponent(index, seat))[-1]['status'], 'accepted')
        hand = consumer.completed()
        self.assertEqual(hand['rank_source'], 'not_required')
        self.assertEqual(hand['settlement']['final_stacks'], [200, 199, 198, 203, 200, 200])
        self.assertEqual(hand['settlement']['payouts'], [0, 0, 0, 5, 0, 0])
        self.assertEqual(hand['settlement']['pots'], [{'amount': 5, 'seats': [3]}])

    def finish_board(self, consumer, index, board, ranks, seats):
        for street, cards in (('flop', board[:3]), ('turn', board[3:4]), ('river', board[4:])):
            consumer.send(event('street_revealed', index, street=street, cards=cards))
            index += 1
            for seat in seats:
                consumer.send(opponent(index, seat, 'check', street))
                index += 1
        consumer.send(event('showdown_result', index, strengths=ranks))
        return consumer.completed()

    def test_showdown_and_repeated_response_walls_use_declared_results(self):
        consumer = self.start('showdown')
        self.assertEqual(consumer.send(event(private_cards=[4, 5]))[0]['action']['kind'], 'call')
        for index, seat in enumerate((4, 5, 0, 1, 2), 1):
            consumer.send(opponent(index, seat, 'check' if seat == 2 else 'call'))
        hand = self.finish_board(consumer, 6, [2, 15, 21, 34, 47], [4, 5, 3, 0, 2, 1],
                                 (1, 2, 4, 5, 0))
        self.assertEqual(hand['settlement']['final_stacks'], [198, 210, 198, 198, 198, 198])
        self.assertEqual(hand['settlement']['payouts'], [0, 12, 0, 0, 0, 0])
        self.assertEqual(hand['rank_source'], 'host_supplied')
        repeated = self.start()
        repeated.send(event())
        repeated.send(opponent(1, 4, 'raise', raise_to=16))
        for index, seat in enumerate((5, 0, 1, 2), 2):
            repeated.send(opponent(index, seat))
        hand = self.finish_board(repeated, 6, [0, 13, 22, 31, 47],
                                 [None, None, None, 0, 1, None], (4,))
        self.assertEqual(hand['settlement']['final_stacks'], [200, 199, 198, 184, 219, 200])
        self.assertEqual(hand['settlement']['payouts'], [0, 0, 0, 0, 35, 0])
        for peer, count in ((consumer, 4), (repeated, 5)):
            decisions = [r['decision'] for r in peer.rows
                         if r['type'] == 'event_result' and r['decision']]
            self.assertEqual([d['selection_reason'] for d in decisions],
                             ['table_hit'] + ['passive_default'] * (count - 1))
            self.assertEqual([d['action_index'] for d in decisions], list(range(1, count + 1)))

    def failed(self, consumer):
        rest = consumer.process.stdout.read()
        self.assertNotEqual(consumer.process.wait(timeout=15), 0)
        self.assertIn(b'REFUSED', consumer.process.stderr.read())
        rows = [*consumer.rows, *(json.loads(line) for line in rest.splitlines())]
        self.assertEqual(rows[-1]['status'], 'failed')
        return rows

    def test_policy_bytes_change_response_and_invalid_entry_never_delivers(self):
        policy = json.loads((FIXTURES / 'fold_blueprint.json').read_bytes())
        actions = ({'kind': 'raise', 'raise_to': 10}, {'kind': 'raise', 'raise_to': 1000}, None)
        for action in actions:
            policy['entries'][0]['action'] = action or {'kind': 'raise', 'raise_to': 8}
            policy['entries'][0]['key']['private_hand'] = [0, 1] if action is None else [48, 49]
            consumer = self.start(policy=wire(policy))
            if action and action['raise_to'] == 1000:
                consumer.process.stdin.write(wire(event()))
                consumer.process.stdin.flush()
                row = consumer.read()
                self.assertEqual(row['type'], 'session_result')
                self.assertEqual(row['failure_reason'], 'invalid_blueprint_entry')
                self.assertEqual(consumer.actions, set())
            else:
                rows = consumer.send(event())
                self.assertEqual(rows[0]['action'], action or {'kind': 'call', 'raise_to': None})
                consumer.process.stdin.close()  # Premature EOF is a failed event, never completion.
            self.failed(consumer)

    def test_minimum_decimal_aggregate_settlement(self):
        stacks = [200, 200, 200, 10**640 - 1001, 200, 200]
        policy = json.loads((FIXTURES / 'fold_blueprint.json').read_bytes())
        key = policy['entries'][0]['key']
        key.update(starting_stacks=stacks, stacks=[200, 199, 198, stacks[3], 200, 200])
        consumer = self.start(policy=wire(policy))
        consumer.send(event(starting_stacks=stacks))
        for index, seat in enumerate((4, 5, 0, 1, 2), 1):
            consumer.send(opponent(index, seat))
        self.assertEqual(consumer.completed()['settlement']['final_stacks'],
                         [200, 199, 198, 10**640 - 998, 200, 200])

    def scheduled(self, mode):
        return self.start(code=self.instrument(f'mode={mode!r}\n' + HOST_SCHEDULE))

    def fold_events(self, consumer):
        consumer.send(event())
        for index, seat in enumerate((4, 5, 0, 1, 2), 1):
            consumer.send(opponent(index, seat))

    def test_public_accounting_is_positive_and_publication_faults_do_not_complete(self):
        consumer = self.scheduled('normal')
        self.fold_events(consumer)
        consumer.completed(positive=True)
        for mode in ('entry', 'closing', 'finalizer', 'body', 'body_and_close',
                     'source_and_close', 'last_short', 'last_failed'):
            with self.subTest(mode=mode):
                consumer = self.scheduled(mode)
                self.fold_events(consumer)
                raw = consumer.process.stdout.read()
                self.assertNotEqual(consumer.process.wait(timeout=15), 0)
                self.assertIn(b'REFUSED', consumer.process.stderr.read())
                if mode.startswith('last_'):
                    parts = raw.split(b'\n')
                    self.assertEqual(json.loads(parts[0])['type'], 'hand_result')
                    self.assertEqual(parts[1], b'{"accountin' if mode == 'last_short' else b'')
                    continue
                rows = [json.loads(line) for line in raw.splitlines()]
                session = rows[-1]
                self.assertEqual(session['status'], 'failed')
                self.assertEqual(session['type'], 'session_result')
                primary = ('trace_write_failed' if mode.startswith('body') else
                           'source_binding_mismatch' if mode == 'source_and_close'
                           else 'clock_invalid')
                self.assertEqual(session['failure_reason'], primary)
                secondary = (['clock_invalid'] if mode in ('body_and_close', 'source_and_close')
                             else [])
                self.assertEqual(session['secondary_failures'], secondary)
                self.assertEqual(session['accounting_complete'], mode == 'body')
                if mode in ('body', 'finalizer'):
                    self.assertGreater(session['terminal_publication_compute_seconds'], 0)
                else:
                    self.assertIsNone(session['terminal_publication_compute_seconds'])
                self.assertEqual(any(row['type'] == 'hand_result' for row in rows),
                                 mode in ('closing', 'finalizer', 'source_and_close'))

    def test_consumer_detects_duplicate_late_start_false_exit_and_false_accounting(self):
        modes = ('duplicate', 'late_start', 'false_exit', 'zero_cost', 'omit_cost', 'wrong_bool')
        for mode in modes:
            consumer = self.scheduled(mode)
            if mode in ('duplicate', 'late_start'):
                consumer.minimum_elapsed = 2_000_000_000 if mode == 'late_start' else 0
                with self.assertRaises(AssertionError):
                    consumer.send(event())
            elif mode == 'false_exit':
                consumer.send(event())
                consumer.process.stdin.close()
                with self.assertRaises(AssertionError):
                    self.failed(consumer)
            else:
                self.fold_events(consumer)
                with self.assertRaises(AssertionError):
                    consumer.completed(positive=True)

    def test_real_reader_rejects_oversized_or_unterminated_frame_without_recovery(self):
        for raw in (wire(event())[:-1], b' ' * 16384 + b'\n' + wire(event()), b'[]\n'):
            consumer = self.start()
            consumer.process.stdin.write(raw)
            consumer.process.stdin.close()
            result = consumer.read()
            self.assertEqual((result['type'], result['event_index']), ('event_result', None))
            self.assertEqual(result['failure']['code'], 'invalid_event')
            self.assertEqual(consumer.actions, set())
            self.failed(consumer)


class DecoderTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(TOOL.is_file(), 'The approved timed frame decoder is not implemented')
        self.tool = load_tool()
        from pontius.v0a import model
        self.model = model

    def decode(self, raw):
        return self.tool.decode_frame(raw, SESSION, self.model)

    def test_exact_members_types_and_owned_arrays_for_all_event_kinds(self):
        cases = [event(), opponent(1, 4),
                 event('street_revealed', 6, street='flop', cards=[2, 15, 21]),
                 event('showdown_result', 23, strengths=[4, 5, 3, 0, 2, 1])]
        for value in cases:
            self.assertEqual(self.decode(wire(value)).kind, value['kind'])
            for key in value:
                changed = dict(value)
                del changed[key]
                with self.subTest(kind=value['kind'], missing=key), \
                        self.assertRaises((TypeError, ValueError)):
                    self.decode(wire(changed))
            for key in ('timestamp', 'hands', 'future_board', 'expected', 'opaque'):
                with self.subTest(extra=key), self.assertRaises((TypeError, ValueError)):
                    self.decode(wire(dict(value, **{key: None})))
            for key, original in value.items():
                for wrong in (None, True, 1.25, {}, []):
                    if type(wrong) is type(original):
                        continue
                    with self.subTest(kind=value['kind'], key=key, wrong=wrong), \
                            self.assertRaises((TypeError, ValueError)):
                        self.decode(wire(dict(value, **{key: wrong})))
        self.assertIs(type(self.decode(wire(event())).starting_stacks), tuple)
        ranks = self.decode(wire(event('showdown_result', 1, strengths=[[1], None, 0, 2, 3, 4])))
        self.assertEqual(ranks.strengths, ((1,), None, 0, 2, 3, 4))
        for action in ({'kind': 'fold'}, {'kind': 'fold', 'raise_to': None, 'extra': 0}):
            with self.assertRaises((TypeError, ValueError)):
                self.decode(wire(event('opponent_action', 1, seat=4,
                                       street='preflop', action=action)))

    def test_strict_json_encoding_framing_and_decimal_token_domain(self):
        raw = wire(event())
        bad = [b'', raw[:-1], b'\xef\xbb\xbf' + raw, raw + b'\r', raw[:-1] + b'\r\n',
               b'\xff\n', b'[]\n', raw[:-2] + b',"kind":"hand_started"}\n',
               raw[:-1] + b' {}\n', b'{"x":NaN}\n', b'{"x":Infinity}\n',
               b'{"x":1.0}\n', b'{"x":' + b'[' * 1500 + b']' * 1500 + b'}\n',
               b'{"x":' + b'1' * 641 + b'}\n']
        for value in bad:
            with self.subTest(raw=value[:30]), \
                    self.assertRaises((TypeError, ValueError, RecursionError)):
                self.decode(value)
        for length in (16383, 16384):
            self.assertEqual(self.decode(raw[:-1] + b' ' * (length - len(raw)) + b'\n').kind,
                             'hand_started')
        with self.assertRaises(ValueError):
            self.decode(raw[:-1] + b' ' * (16385 - len(raw)) + b'\n')
        negative = event('showdown_result', 1, strengths=[-(10**639), 1, 2, 3, 4, 5])
        self.assertEqual(self.decode(wire(negative)).strengths[0], -(10**639))

    def test_aggregate_chip_bound_is_stricter_than_individual_integer_bound(self):
        limit = 10**640
        admitted = self.decode(wire(event(starting_stacks=[limit - 6] + [1] * 5)))
        self.assertEqual(sum(admitted.starting_stacks), limit - 1)
        for stacks in ([limit - 5] + [1] * 5, [limit - 4] + [1] * 5, [10**639 * 2] * 6):
            with self.assertRaises(ValueError):
                self.decode(wire(event(starting_stacks=stacks)))


class ManualClock:
    def __init__(self):
        self.ns, self.invalid = 1_000_000_000, False

    def __call__(self):
        return None if self.invalid else self.ns


class RuntimeBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.tool = load_tool()
        from pontius.blueprint_artifact import codec
        from pontius.v0a import model, runtime, clock, trace
        self.model, self.core, self.clock, self.trace = model, runtime, clock, trace
        self.policy = codec.decode_blueprint((FIXTURES / 'fold_blueprint.json').read_bytes())

    def runtime(self, source, *, begin=True):
        reader, writer = os.pipe()
        content = bytearray()
        def consume():
            with os.fdopen(reader, 'rb') as stream:
                content.extend(stream.read())
        thread = threading.Thread(target=consume)
        thread.start()
        closed = []
        def finish():
            if not closed:
                os.close(writer)
                closed.append(True)
                thread.join(timeout=15)
                self.assertFalse(thread.is_alive())
            return bytes(content)
        self.addCleanup(finish)
        output = self.tool.PipeOutput(SESSION, self.model, self.trace, writer)
        runtime = self.tool.runtime_type(self.model, self.core, self.clock)(
            session_id=SESSION, blueprint=self.policy, mailbox=output, clock=source)
        if begin:
            runtime.begin_host_accounting()
        return runtime, output, finish

    def test_initial_dispatch_clock_failure_matches_the_inherited_shell(self):
        clock = ManualClock()
        clock.invalid = True
        runtime, output, finish = self.runtime(clock, begin=False)
        result = runtime.dispatch_frame(wire(event()))
        self.assertEqual(result.failure.code.value, 'clock_invalid')
        self.assertIsNone(result.failure.timing)
        self.assertEqual(finish(), b'')

    def test_decode_delay_enters_14_second_boundary_at_each_nanosecond_edge(self):
        original = self.tool.decode_frame
        for elapsed in (13_999_999_999, 14_000_000_000, 14_000_000_001):
            clock = ManualClock()
            runtime, output, finish = self.runtime(clock)
            def delayed(raw, session, model):
                clock.ns += elapsed
                return original(raw, session, model)
            with patch.object(self.tool, 'decode_frame', delayed):
                result = runtime.dispatch_frame(wire(event()))
            self.assertEqual(result.decision.timing.elapsed_ns, elapsed)
            self.assertEqual(result.decision.timing.work_cutoff_crossed, elapsed >= 14_000_000_000)
            self.assertEqual(result.status, 'decided' if elapsed < 14_000_000_000 else 'failed')
            self.assertEqual(json.loads(finish())['action'], {'kind': 'raise', 'raise_to': 8})

    def test_real_emission_at_15_second_edges_and_post_write_clock_fault(self):
        native = os.write
        for elapsed in (14_999_999_999, 15_000_000_000, 15_000_000_001, None):
            clock = ManualClock()
            runtime, output, finish = self.runtime(clock)
            def publish(fd, raw):
                count = native(fd, raw)
                if elapsed is None:
                    clock.invalid = True
                else:
                    clock.ns += elapsed
                return count
            with patch.object(self.tool.os, 'write', publish):
                result = runtime.dispatch_frame(wire(event()))
            self.assertEqual(json.loads(finish())['action_index'], 1)
            self.assertEqual(runtime.accepted_delivery_count, 1)
            self.assertIsNotNone(result.decision)
            self.assertEqual(result.decision.timing.elapsed_ns, elapsed)
            if elapsed is None or elapsed > 15_000_000_000:
                self.assertEqual(result.failure.delivery_status.value, 'accepted')
                self.assertEqual(result.failure.code.value, 'clock_invalid' if elapsed is None
                                 else 'action_deadline_exceeded')
            else:
                self.assertEqual(result.status, 'decided')

    def test_native_short_and_failed_write_are_ambiguous_and_identity_is_not_retried(self):
        native = os.write
        for short in (True, False):
            runtime, output, finish = self.runtime(ManualClock())
            def publish(fd, raw):
                return native(fd if short else -1, raw[:11])
            with patch.object(self.tool.os, 'write', publish):
                result = runtime.dispatch_frame(wire(event()))
            self.assertEqual(finish(), b'{"action":{' if short else b'')
            self.assertEqual(result.failure.delivery_status.value, 'unknown')
            self.assertEqual(runtime.accepted_delivery_count, 0)
            envelope = self.model.ActionEnvelope(SESSION, 1, 3, 'preflop',
                                                  self.model.HandAction('raise', 8))
            with self.assertRaises(self.model.MailboxRejectionError):
                output.deliver(envelope)

    def test_decoder_error_precedes_cleanup_clock_fault_and_keeps_null_admission(self):
        clock = ManualClock()
        runtime, output, finish = self.runtime(clock)
        def invalid(*args):
            clock.invalid = True
            raise ValueError('declared decoder failure')
        with patch.object(self.tool, 'decode_frame', invalid):
            result = runtime.dispatch_frame(b'invalid\n')
        self.assertEqual([code.value for code in runtime.closure_failures],
                         ['invalid_event', 'clock_invalid'])
        self.assertIsNone(runtime.event_index)
        self.assertIsNone(result.failure.event_index)
        self.assertIsNone(runtime.accounting().preparation_compute_seconds)
        self.assertEqual(finish(), b'')

    def test_fresh_repeated_walls_and_non_action_preparation_exclude_idle(self):
        clock = ManualClock()
        runtime, output, finish = self.runtime(clock)
        original = self.tool.decode_frame
        def delayed(*args):
            clock.ns += 100
            return original(*args)
        decisions = []
        values = [event(), opponent(1, 4, 'raise', raise_to=16)]
        values += [opponent(index, seat) for index, seat in enumerate((5, 0, 1, 2), 2)]
        with patch.object(self.tool, 'decode_frame', delayed):
            for value in values:
                clock.ns += 20_000_000_000  # Caller idle between complete event receipts.
                result = runtime.dispatch_frame(wire(value))
                if result.decision:
                    decisions.append(result.decision)
        self.assertEqual([d.timing.elapsed_ns for d in decisions], [100, 100])
        self.assertGreater(decisions[1].timing.wall_start_ns, decisions[0].timing.wall_start_ns)
        self.assertEqual(runtime.accounting().preparation_compute_seconds, 400 / 1_000_000_000)
        self.assertEqual(len(finish().splitlines()), 2)

    def test_real_runtime_refuses_event_order_hidden_cards_and_terminal_misuse(self):
        cases = [opponent(2, 4), opponent(1, 3), opponent(1, 5), opponent(1, 4, street='flop'),
                 event('showdown_result', 1, strengths=[0, 1, 2, 3, 4, 5]),
                 event('street_revealed', 1, street='flop', cards=[48, 2, 3]),
                 event(private_cards=[4, 4]), event(private_cards=[-1, 53]),
                 event(hand_id='other'), event(controlled_seat=True)]
        for value in cases:
            runtime, output, finish = self.runtime(ManualClock())
            if value['kind'] != 'hand_started':
                runtime.dispatch_frame(wire(event()))
            result = runtime.dispatch_frame(wire(value))
            self.assertEqual(result.status, 'failed', value)
            self.assertIn(result.failure.code.value, ('invalid_event', 'event_order'))
            finish()

    def test_card_overlap_and_rank_refusals_reach_their_admissible_streets(self):
        prefix = [event(), opponent(1, 4, 'raise', raise_to=16)]
        prefix += [opponent(i, s) for i, s in enumerate((5, 0, 1, 2), 2)]
        flop = event('street_revealed', 6, street='flop', cards=[0, 13, 22])
        turn = event('street_revealed', 8, street='turn', cards=[31])
        river = event('street_revealed', 10, street='river', cards=[47])
        flop_done = prefix + [flop, opponent(7, 4, 'check', 'flop')]
        river_done = flop_done + [turn, opponent(9, 4, 'check', 'turn'),
                                 river, opponent(11, 4, 'check', 'river')]
        cases = [(prefix, dict(flop, cards=[48, 13, 22])),
                 (flop_done, dict(turn, cards=[0])), (prefix, dict(turn, event_index=6))]
        cases += [(river_done, event('showdown_result', 12, strengths=ranks)) for ranks in
                  ([0, 1, 2, 3, 4, 5], [None, None, None, [0], 1, None], [None] * 6)]
        for history, invalid in cases:
            runtime, output, finish = self.runtime(ManualClock())
            for value in history:
                self.assertNotEqual(runtime.dispatch_frame(wire(value)).status, 'failed')
            self.assertEqual(runtime.dispatch_frame(wire(invalid)).status, 'failed')
            self.assertEqual(len(finish().splitlines()), 5 if history is river_done else
                             3 if history is flop_done else 2)


if __name__ == '__main__':
    unittest.main()
