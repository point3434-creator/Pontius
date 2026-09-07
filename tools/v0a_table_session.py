"""Finite watch-first correctness session around the sealed one-hand host."""
from __future__ import annotations
import argparse
import base64
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import types

VERSION = 'pontius-v0a-table-session-v1'
PREFIX = VERSION + '-correctness-'
HOST = 'tools/v0a_table_host.py'
SELF = 'tools/v0a_table_session.py'
HOST_BLOB = '6ec8a162b053158203663c48e82314b10750f962'
ALIAS = 'pontius_v0a_table_session_host'


class Refusal(ValueError):
    def __init__(self, code):
        super().__init__(code)
        self.code = code


def require(condition, code='source_invalid'):
    if not condition:
        raise Refusal(code)


def encode(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)
            + '\n').encode('utf-8')


def regular(path, directory=False):
    require(path.is_absolute() and len(path.drive) == 2 and '..' not in path.parts)
    for current in (*path.parents, path):
        info = current.lstat()
        require(not info.st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT
                and (stat.S_ISDIR(info.st_mode) if current != path or directory
                     else stat.S_ISREG(info.st_mode)))
    return path


def source_bytes(path):
    before = regular(path).stat()
    with path.open('rb') as stream:
        raw = stream.read(1048577)
    after = regular(path).stat()
    identity = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns)
    require(identity(before) == identity(after) and 0 < len(raw) <= 1048576)
    return raw, identity(after)


class Admission:
    def __init__(self, repo):
        require(os.name == 'nt' and sys.implementation.name == 'cpython'
                and sys.dont_write_bytecode and sys.flags.safe_path)
        require(not any(n == 'pontius' or n.startswith('pontius.') for n in sys.modules)
                and ALIAS not in sys.modules)
        self.repo = regular(repo, True)
        require(repo.drive.upper() == 'D:' and Path(__file__).absolute() == repo / SELF)
        regular(Path(sys.executable))
        self.git = regular(Path(os.environ.get('PONTIUS_GIT', '')))
        self.env = {k: v for k, v in os.environ.items()
                    if not k.upper().startswith(('GIT_', 'PYTHON', 'PONTIUS_'))}
        self.commit = self.command('rev-parse', '--verify', 'HEAD^{commit}').decode().strip()
        require(re.fullmatch('[0-9a-f]{40}', self.commit))
        self.expected = {}
        for name in (SELF, HOST):
            row = self.command('ls-tree', self.commit, '--', name).split()
            require(len(row) == 4 and row[0] in (b'100644', b'100755') and row[1] == b'blob'
                    and row[3] == name.encode())
            if name == HOST:
                require(row[2].decode() == HOST_BLOB)
            raw = self.command('cat-file', 'blob', row[2].decode())
            observed = source_bytes(repo / name)
            require(observed[0] == raw)
            self.expected[name] = observed
        self.check()
        host = types.ModuleType(ALIAS)
        host.__file__, host.__package__ = str(repo / HOST), ''
        sys.modules[ALIAS] = host
        exec(compile(self.expected[HOST][0], host.__file__, 'exec'), host.__dict__)
        self.host = host
        self.source = host.Source(repo)
        self.modules = self.source.load()
        self.check()

    def command(self, *args):
        result = subprocess.run([str(self.git), '--no-replace-objects', '--no-optional-locks',
            '-C', str(self.repo), *args], env=self.env, capture_output=True, timeout=30)
        require(result.returncode == 0)
        return result.stdout

    def check(self):
        try:
            require(self.command('rev-parse', '--verify', 'HEAD^{commit}').decode().strip()
                    == self.commit)
            for name, expected in self.expected.items():
                require(source_bytes(self.repo / name) == expected)
            if hasattr(self, 'source'):
                self.source.check()
        except (OSError, ValueError, subprocess.SubprocessError) as error:
            raise Refusal('source_invalid') from error


class Schedule:
    def __init__(self, raw, host, modules):
        self.host, self.modules = host, modules
        value = host.decode_json(raw, code='input_invalid', digits=7)
        require(type(value) is dict and set(value) == set(('version button controlled_seat '
            'starting_stacks small_blind big_blind opponents hands').split()), 'input_invalid')
        require(value['version'] == VERSION and type(value['hands']) is list
                and 1 <= len(value['hands']) <= 16, 'input_invalid')
        require(type(value['starting_stacks']) is list, 'input_invalid')
        self.common = {k: v for k, v in value.items() if k != 'hands'}
        self.common['version'] = host.INPUT_VERSION
        self.hands = value['hands']
        for index, deal in enumerate(self.hands):
            require(type(deal) is dict and set(deal) == {'private_hands', 'board_runout'},
                    'input_invalid')
            self.derive(index, value['starting_stacks'], value['button'])

    def derive(self, index, stacks, button):
        raw = encode(dict(self.common, **self.hands[index], starting_stacks=list(stacks),
                          button=button))
        return self.host.TableInput.decode(raw, self.modules), raw


@dataclass(frozen=True)
class Visible:
    ordinal: int
    button: int
    bot: int
    cards: tuple
    street: str
    board: tuple
    stacks: tuple
    actions: tuple


def action_values(rows):
    return tuple((r['index'], r['seat'], r['street'], r['action']['kind'],
                  r['action']['raise_to'], r['origin']) for r in rows)


def visible(table, ordinal, cursor):
    view = table.views[table.config.controlled_seat]
    fmt = table.modules.cards.format_card
    return Visible(ordinal, table.config.button, table.config.controlled_seat,
        tuple(fmt(c) for c in view.private_hand), view.street.value,
        tuple(fmt(c) for c in view.board), tuple(table.state.stacks),
        action_values(table.applied_actions[cursor:]))


class Renderer:
    def __init__(self, fd):
        self.fd, self.written, self.usable, self.last_street = fd, 0, True, None

    def line(self, text):
        try:
            require(self.usable, 'output_failed')
            raw = (text + '\n').encode('ascii')
            require(len(raw) <= 4096 and self.written + len(raw) <= 4194304, 'output_failed')
            self.written += len(raw)
            require(os.write(self.fd, raw) == len(raw), 'output_failed')
        except BaseException:
            self.usable = False
            raise

    def heading(self, view, total):
        self.last_street = None
        self.line(f'Hand {view.ordinal}/{total} button {view.button} bot seat {view.bot}')
        self.line('Cards: ' + ' '.join(view.cards))

    def actions(self, rows, prefix=''):
        for index, seat, street, kind, amount, origin in rows:
            extra = '' if amount is None else f' to {amount}'
            self.line(f'{prefix}action {index} seat {seat} {street} {kind}{extra} ({origin})')

    def update(self, view):
        current = (view.ordinal, view.street, view.board)
        if current != self.last_street:
            self.last_street = current
            self.line(view.street + ' board: ' + ' '.join(view.board))
        self.actions(view.actions)

    def settled(self, payouts, stacks):
        self.line('Payouts: ' + ' '.join(map(str, payouts)))
        self.line('Stacks: ' + ' '.join(map(str, stacks)))

    def prompt(self):
        self.line('Next: Enter/n for next hand, q to quit')

    def final(self, status, reason, count, stacks):
        self.line(f'Session {status}: {reason or status}; completed hands {count}')
        if stacks is not None:
            self.line('Final stacks: ' + ' '.join(map(str, stacks)))


def read_command():
    return sys.stdin.buffer.readline(8)


def command_kind(raw):
    require(type(raw) is bytes, 'command_invalid')
    if raw in (b'\n', b'\r\n', b'n\n', b'n\r\n'):
        return 'next'
    if raw in (b'q\n', b'q\r\n'):
        return 'quit'
    if raw == b'':
        return 'eof'
    raise Refusal('command_invalid')


class Session:
    def __init__(self, args, renderer=None, command=None):
        self.args, self.renderer, self.command = args, renderer, command
        self.admission, self.active = None, None
        self.failures = []
        self.strategy = getattr(args, 'strategy', 'blueprint-v1')
        self.baseline = self.strategy == 'baseline-rules-v1'
        self.prefix = 'pontius-v0a-table-session-v2-correctness-' if self.baseline else PREFIX
        self.identity = None
        self.report = dict(version='pontius-v0a-table-session-result-v1',
            session_id=args.session_id, status='failed', stop_reason=None, failure_reason=None,
            secondary_failures=[], source_commit=None, input_sha256=None,
            blueprint_artifact_sha256=None, blueprint_sha256=None, requested_hands=None,
            completed_hands=0, next_button=None, carried_stacks=None, hands=[])
        if self.baseline:
            self.report.update(version='pontius-v0a-table-session-result-v2',
                               provider=None, config_sha256=None)

    def add_error(self, error, failures, phase):
        if isinstance(error, KeyboardInterrupt):
            code, secondary = 'interrupted', ()
        elif isinstance(error, Refusal) or (self.admission is not None
                and isinstance(error, self.admission.host.HostRefusal)):
            code, secondary = error.code, getattr(error, 'secondary', ())
        else:
            code, secondary = phase, ()
        for item in (code, *secondary):
            if item not in failures:
                failures.append(item)

    def prepare(self):
        require(re.fullmatch(re.escape(self.prefix) + '[A-Za-z0-9_-]{1,40}', self.args.session_id),
                'input_invalid')
        self.admission = Admission(Path.cwd())
        self.host, self.modules = self.admission.host, self.admission.modules
        self.report['source_commit'] = self.admission.commit
        self.session_input = self.host.OwnedInput(Path(self.args.session), 16384)
        self.blueprint_input = self.host.OwnedInput(Path(self.args.blueprint), 1048576)
        self.report.update(input_sha256=hashlib.sha256(self.session_input.raw).hexdigest(),
            blueprint_artifact_sha256=hashlib.sha256(self.blueprint_input.raw).hexdigest())
        self.schedule = Schedule(self.session_input.raw, self.host, self.modules)
        try:
            blueprint = self.modules.codec.decode_blueprint(self.blueprint_input.raw)
        except (ValueError, TypeError) as error:
            raise Refusal('input_invalid') from error
        self.report['blueprint_sha256'] = blueprint.digest
        self.blueprint = blueprint
        if self.baseline:
            self.identity = self.modules.providers.make_provider(self.strategy, blueprint).identity
            self.report.update(provider=self.identity.provider,
                               config_sha256=self.identity.config_sha256)
            if self.renderer is not None:
                self.renderer.line('Strategy: ' + self.identity.provider)
        self.report.update(requested_hands=len(self.schedule.hands),
            next_button=self.schedule.common['button'],
            carried_stacks=list(self.schedule.common['starting_stacks']))

    def validate(self):
        self.admission.check()
        self.session_input.check()
        self.blueprint_input.check()

    def play_hand(self, index):
        self.validate()
        config, raw = self.schedule.derive(index, self.report['carried_stacks'],
                                           self.report['next_button'])
        suffix = self.args.session_id[len(self.prefix):] + '-h%02d' % (index + 1)
        protocol = 'pontius-v0a-event-interface-v2' if self.baseline else self.host.PROTOCOL
        child_id = protocol + '-correctness-table-' + suffix
        table = self.host.Table(config, self.modules, child_id)
        hand = dict(version='pontius-v0a-table-session-hand-result-v1',
            session_id='pontius-v0a-table-host-v1-correctness-' + suffix, status='failed',
            failure_reason=None, secondary_failures=[],
            input_sha256=hashlib.sha256(raw).hexdigest(),
            blueprint_artifact_sha256=self.report['blueprint_artifact_sha256'],
            blueprint_sha256=self.report['blueprint_sha256'], source_commit=self.admission.commit,
            applied_actions=table.applied_actions, settlement=None, child_exit_code=None,
            child_stdout_base64='', child_stderr_base64='', capture_truncated=False)
        if self.baseline:
            hand.update(version='pontius-v0a-table-session-hand-result-v2',
                session_id='pontius-v0a-table-host-v2-correctness-' + suffix,
                provider=self.identity.provider, config_sha256=self.identity.config_sha256)
        entry = dict(ordinal=index + 1, button=config.button,
                     starting_stacks=list(config.starting_stacks), result=hand)
        self.report['hands'].append(entry)
        self.active = entry
        failures, connection, provisional, cursor = self.host.Failures(), None, None, 0
        phase = 'process_start_failed'
        try:
            connection = self.host.ChildConnection(self.admission.source, self.blueprint_input.path,
                                                   child_id, failures, self.strategy)
            consumer = self.host.WireConsumer(connection, self.admission.source, table,
                self.report['blueprint_artifact_sha256'], self.report['blueprint_sha256'],
                self.identity, self.blueprint if self.baseline else None)
            phase = 'protocol_invalid'
            consumer.ready()
            if self.renderer is not None:
                phase = 'output_failed'
                self.renderer.heading(visible(table, index + 1, 0), self.report['requested_hands'])
            event = table.start_event()
            while event is not None:
                phase = 'protocol_invalid'
                consumer.exchange(event)
                if self.renderer is not None:
                    phase = 'output_failed'
                    view = visible(table, index + 1, cursor)
                    cursor = len(table.applied_actions)
                    self.renderer.update(view)
                    if self.baseline and table.bot_index in consumer.reasons:
                        self.renderer.line('Reason: ' + consumer.reasons.pop(table.bot_index))
                phase = 'protocol_invalid'
                event = table.next_event()
            provisional = consumer.complete()
            self.validate()
        except BaseException as error:
            if isinstance(error, self.host.HostRefusal) and error.connection is not None:
                connection = error.connection
            self.add_error(error, failures.items, phase)
        finally:
            if connection is not None:
                try:
                    connection.finish(provisional is not None and not failures.items)
                except BaseException as error:
                    self.add_error(error, failures.items, 'cleanup_failed')
                hand.update(child_exit_code=connection.exit_code,
                    child_stdout_base64=base64.b64encode(connection.stdout).decode('ascii'),
                    child_stderr_base64=base64.b64encode(connection.stderr).decode('ascii'),
                    capture_truncated=connection.truncated)
        try:
            self.validate()
            if not failures.items:
                require(provisional is not None and type(hand['child_exit_code']) is int
                        and hand['child_exit_code'] == 0 and not hand['capture_truncated'],
                        'cleanup_failed')
        except BaseException as error:
            self.add_error(error, failures.items, 'source_invalid')
        if failures.items:
            if self.renderer is not None and getattr(self.renderer, 'usable', True):
                try:
                    remaining = action_values(table.applied_actions[cursor:])
                    cursor = len(table.applied_actions)
                    self.renderer.actions(remaining, 'applied-before-failure ')
                except BaseException as error:
                    self.add_error(error, failures.items, 'output_failed')
            hand.update(failure_reason=failures.items[0], secondary_failures=failures.items[1:])
            self.failures.extend(item for item in failures.items if item not in self.failures)
            return None
        return dict(entry, result=dict(hand, status='completed', settlement=provisional))

    def run(self):
        phase = 'source_invalid'
        try:
            if self.admission is None:
                self.prepare()
            for index in range(len(self.schedule.hands)):
                phase = 'input_invalid'
                accepted = self.play_hand(index)
                if accepted is None:
                    break
                self.report.update(hands=[*self.report['hands'][:-1], accepted],
                    carried_stacks=list(accepted['result']['settlement']['final_stacks']),
                    next_button=(accepted['button'] + 1) % 6, completed_hands=index + 1)
                self.active = None
                if self.renderer is not None:
                    phase = 'output_failed'
                    self.renderer.settled(tuple(accepted['result']['settlement']['payouts']),
                                          tuple(self.report['carried_stacks']))
                if index + 1 == len(self.schedule.hands):
                    self.report['status'] = 'completed'
                    break
                if any(s < self.schedule.common['big_blind']
                       for s in self.report['carried_stacks']):
                    self.report.update(status='stopped', stop_reason='insufficient_stacks')
                    break
                if not self.args.auto:
                    if self.renderer is not None:
                        phase = 'output_failed'
                        self.renderer.prompt()
                    phase = 'input_failed'
                    command = command_kind((self.command or read_command)())
                    if command != 'next':
                        self.report.update(status='stopped', stop_reason=command)
                        break
            self.validate()
        except BaseException as error:
            self.add_error(error, self.failures, phase)
            if self.active is not None:
                hand = self.active['result']
                hand.update(failure_reason=self.failures[0], secondary_failures=self.failures[1:])
        if self.failures:
            self.report.update(
                status='interrupted' if self.failures[0] == 'interrupted' else 'failed',
                failure_reason=self.failures[0], secondary_failures=list(self.failures[1:]),
                stop_reason=None)
        return self.report


def arguments(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    for flag in ('session', 'blueprint', 'session-id'):
        parser.add_argument('--' + flag, required=True)
    parser.add_argument('--auto', action='store_true')
    parser.add_argument('--strategy', choices=('blueprint-v1', 'baseline-rules-v1'),
                        default='blueprint-v1')
    parser.add_argument('--format', choices=('text', 'json'), default='text')
    args = parser.parse_args(argv)
    if args.format == 'json' and not args.auto:
        parser.error('--format json requires --auto')
    return args


def main(argv=None):
    args = arguments(argv)
    renderer = Renderer(sys.stdout.fileno()) if args.format == 'text' else None
    report = Session(args, renderer).run()
    try:
        if renderer is not None:
            renderer.final(report['status'], report['failure_reason'] or report['stop_reason'],
                           report['completed_hands'], report['carried_stacks'])
        else:
            raw = bytearray()
            encoder = json.JSONEncoder(sort_keys=True, separators=(',', ':'), allow_nan=False)
            for chunk in encoder.iterencode(report):
                part = chunk.encode('utf-8')
                require(len(raw) + len(part) + 1 <= 67108864, 'output_failed')
                raw.extend(part)
            raw.extend(b'\n')
            require(os.write(sys.stdout.fileno(), raw) == len(raw), 'output_failed')
    except BaseException:
        try:
            os.write(sys.stderr.fileno(), b'REFUSED output_failed\n')
        except BaseException:
            pass
        return 1
    return 130 if report['status'] == 'interrupted' else int(report['status'] == 'failed')


if __name__ == '__main__':
    raise SystemExit(main())
