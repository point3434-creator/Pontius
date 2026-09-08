"""Finite one-hand reactive correctness host; no operating or training authority."""
from __future__ import annotations

import argparse
import base64
import ctypes
from dataclasses import dataclass
import hashlib
import json
import math
import os
from pathlib import Path
import queue
import shutil
import re
import stat
import subprocess
import sys
import threading
import time

INPUT_VERSION = 'pontius-v0a-table-input-v1'
PROTOCOL = 'pontius-v0a-event-interface-v1'
PREFIX = 'pontius-v0a-table-host-v1-correctness-'
POLICIES = ('passive', 'fold_to_bet', 'min_raise_once', 'shove_once')
EVENT_LIMIT = ACTION_LIMIT = 256
CREATE_SUSPENDED = 0x00000004


class HostRefusal(ValueError):
    def __init__(self, code, connection=None, secondary=()):
        super().__init__(code)
        self.code = code
        self.connection = connection
        self.secondary = secondary


def require(condition, code='protocol_invalid'):
    if not condition:
        raise HostRefusal(code)


def integer(value, minimum=0, maximum=10**640 - 1):
    return type(value) is int and minimum <= value <= maximum


def exact_object(value, keys, code='protocol_invalid'):
    require(type(value) is dict and set(value) == set(keys.split()), code)
    return value


def decode_json(raw, *, code, digits, floats=False):
    def number(token):
        require(len(token.lstrip('-')) <= digits, code)
        return int(token)

    def reject(token):
        raise HostRefusal(code)

    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, code)
            result[key] = value
        return result

    try:
        require(type(raw) is bytes and 0 < len(raw) <= 16384 and b'\r' not in raw
                and not raw.startswith(b'\xef\xbb\xbf'), code)
        depth, quoted, escaped = 0, False, False
        for byte in raw:
            if quoted:
                if escaped:
                    escaped = False
                elif byte == 92:
                    escaped = True
                elif byte == 34:
                    quoted = False
            elif byte == 34:
                quoted = True
            elif byte in (91, 123):
                depth += 1
                require(depth <= 8, code)
            elif byte in (93, 125):
                depth -= 1
        return json.loads(raw.decode('utf-8'), parse_int=number,
                          parse_float=float if floats else reject, parse_constant=reject,
                          object_pairs_hook=pairs)
    except (ValueError, TypeError, RecursionError) as error:
        raise HostRefusal(code) from error


@dataclass(frozen=True)
class Modules:
    codec: object
    betting: object
    cards: object
    spine: object
    model: object
    trace: object
    provider_model: object = None
    providers: object = None
    provider_codec: object = None


def checked_path(path, *, directory=False, d_local=False):
    require(path.is_absolute() and len(path.drive) == 2 and '..' not in path.parts
            and (not d_local or path.drive.upper() == 'D:'), 'source_invalid')
    for current in (*path.parents, path):
        info = current.lstat()
        want_dir = current != path or directory
        require(not info.st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT
                and (stat.S_ISDIR(info.st_mode) if want_dir else stat.S_ISREG(info.st_mode)),
                'source_invalid')
    return path


class OwnedInput:
    def __init__(self, path, limit):
        self.path, self.limit = path, limit
        self.raw, self.identity = self.read()

    def read(self):
        try:
            checked_path(self.path)
            before = self.path.stat()
            with self.path.open('rb') as stream:
                raw = stream.read(self.limit + 1)
            after = self.path.stat()
            def identity(info):
                return info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns
            require(identity(before) == identity(after) and 0 < len(raw) <= self.limit,
                    'input_invalid')
            return raw, identity(after)
        except (OSError, ValueError) as error:
            raise HostRefusal('input_invalid') from error

    def check(self):
        require(self.read() == (self.raw, self.identity), 'input_invalid')


class Source:
    """A source identity shared by every hand in a run."""
    def __init__(self, repo, *, reviewed_commit=None, development=False):
        self.repo = Path(repo).resolve()
        sys.path.insert(0, str(self.repo / 'src'))
        from pontius.execution import begin_run, CONTEXT_ENV
        self.context = begin_run(self.repo, reviewed_commit=reviewed_commit,
                                 allow_working_tree=development,
                                 inherited=os.environ.get(CONTEXT_ENV))
        self.commit = self.context['commit']
        self.manifest = self.context['source_sha256']
        self.python = Path(sys.executable).resolve()
        self.git = os.environ.get('PONTIUS_GIT') or shutil.which('git')
        self.child_manifest = self.manifest

    def load(self):
        sys.path.insert(0, str(self.repo / 'src'))
        import pontius.blueprint_artifact.codec as codec
        import pontius.no_limit_betting as betting
        import pontius.holdem_cards as cards
        import pontius.legal_decision_spine_v2 as spine
        import pontius.v0a.model as model
        import pontius.v0a.trace as trace
        import pontius.decision_provider.model as provider_model
        import pontius.decision_provider.providers as providers
        import pontius.decision_provider.codec as provider_codec
        return Modules(codec, betting, cards, spine, model, trace,
                       provider_model, providers, provider_codec)



@dataclass(frozen=True)
class TableInput:
    button: int
    controlled_seat: int
    starting_stacks: tuple
    small_blind: int
    big_blind: int
    deal: object
    opponents: tuple

    @classmethod
    def decode(cls, raw, modules):
        code = 'input_invalid'
        value = exact_object(decode_json(raw, code=code, digits=7),
                             'version button controlled_seat starting_stacks small_blind '
                             'big_blind private_hands board_runout opponents', code)
        require(value['version'] == INPUT_VERSION, code)
        require(all(integer(value[k], 0, 5) for k in ('button', 'controlled_seat')), code)
        stacks = value['starting_stacks']
        require(type(stacks) is list and len(stacks) == 6
                and all(integer(n, 1, 1000000) for n in stacks) and sum(stacks) <= 1000000, code)
        small, big = value['small_blind'], value['big_blind']
        require(integer(small, 1, 1000000) and integer(big, 1, 1000000)
                and small < big and all(n >= big for n in stacks), code)
        hands, board, opponents = (value[k] for k in ('private_hands', 'board_runout', 'opponents'))
        require(type(hands) is list and len(hands) == 6 and all(type(h) is list and len(h) == 2
                and all(integer(c, 0, 51) for c in h) for h in hands), code)
        require(type(board) is list and len(board) == 5
                and all(integer(c, 0, 51) for c in board), code)
        require(type(opponents) is list and len(opponents) == 6 and all(
            p is None if s == value['controlled_seat'] else type(p) is str and p in POLICIES
            for s, p in enumerate(opponents)), code)
        try:
            deal = modules.cards.SixSeatHoldemDeal(tuple(tuple(h) for h in hands), tuple(board))
        except (ValueError, TypeError) as error:
            raise HostRefusal(code) from error
        return cls(value['button'], value['controlled_seat'], tuple(stacks), small, big,
                   deal, tuple(opponents))


def select_opponent(policy, view, state, legal, modules):
    """Only this seat's observation and public history enter a controller."""
    require(policy in POLICIES and view.controlled_seat == legal.acting_seat, 'action_invalid')
    prior = [row for row in state.history if row.seat == legal.acting_seat]
    first = not any(row.street == state.street for row in prior)
    if legal.can_raise and ((policy == 'min_raise_once' and first)
                            or (policy == 'shove_once' and not prior)):
        amount = (legal.raise_bounds.minimum_raise_to if policy == 'min_raise_once'
                  else legal.raise_bounds.maximum_raise_to)
        return modules.model.HandAction('raise', amount)
    kind = ('check' if legal.can_check else 'fold' if policy == 'fold_to_bet'
            else 'call' if legal.can_call else 'fold')
    return modules.model.HandAction(kind, None)


class Table:
    """Authoritative dealer state, separate from the external controlled player."""
    def __init__(self, config, modules, child_id):
        self.config, self.modules, self.child_id = config, modules, child_id
        self.state = modules.betting.NoLimitBettingState.new_hand(button=config.button,
            starting_stacks=config.starting_stacks, small_blind=config.small_blind,
            big_blind=config.big_blind)
        self.views = tuple(modules.cards.OneSeatCardState.preflop(
            controlled_seat=s, private_hand=config.deal.hand(s)) for s in range(6))
        self.applied_actions = []
        self.event_index, self.bot_index, self.street_index = -1, 0, 0
        self.strengths, self.showdown_sent = None, False

    def event(self, kind, **values):
        require(self.event_index + 1 < EVENT_LIMIT, 'host_limit')
        self.event_index += 1
        return dict(kind=kind, schema_version='pontius-v0a-event-v1', hand_id=self.child_id,
                    event_index=self.event_index, **values)

    def start_event(self):
        require(self.event_index == -1, 'protocol_invalid')
        c = self.config
        return self.event('hand_started', button=c.button, controlled_seat=c.controlled_seat,
                          starting_stacks=list(c.starting_stacks), small_blind=c.small_blind,
                          big_blind=c.big_blind, private_cards=list(c.deal.hand(c.controlled_seat)))

    def expects_action(self):
        return not self.state.is_terminal and self.state.acting_seat == self.config.controlled_seat

    def apply(self, action, origin):
        require(len(self.applied_actions) < ACTION_LIMIT, 'host_limit')
        seat, street = self.state.acting_seat, self.state.street.value
        try:
            changed = self.state.apply_action(action.to_betting_action())
        except (ValueError, TypeError) as error:
            raise HostRefusal('action_invalid') from error
        self.state = changed
        self.applied_actions.append(dict(index=len(self.applied_actions), seat=seat,
            street=street, action=self.modules.trace.action_payload(action), origin=origin))

    def apply_bot(self, action):
        require(self.expects_action(), 'action_invalid')
        self.apply(action, 'bot')
        self.bot_index += 1
        self.street_index += 1

    def next_event(self):
        if self.state.terminal_reason == self.modules.betting.TerminalReason.FOLD:
            return None
        if self.showdown_sent:
            return None
        require(self.event_index + 1 < EVENT_LIMIT, 'host_limit')
        require(not self.expects_action(), 'action_invalid')
        if self.state.round_complete:
            if self.state.street.value == 'river':
                if not self.state.is_terminal:
                    self.state = self.state.advance_street()
                self.strengths = self.config.deal.showdown_strengths(self.state.live_seats)
                self.showdown_sent = True
                return self.event('showdown_result', strengths=[None if r is None else list(r)
                                                               for r in self.strengths])
            self.state = self.state.advance_street()
            self.street_index = 0
            self.views = tuple(self.modules.cards.OneSeatCardState(s, self.config.deal.hand(s),
                self.state.street, self.config.deal.public_cards(self.state.street))
                for s in range(6))
            return self.event('street_revealed', street=self.state.street.value,
                              cards=list(self.config.deal.reveal_for(self.state.street)))
        seat = self.state.acting_seat
        action = select_opponent(self.config.opponents[seat], self.views[seat], self.state,
                                 self.state.legal_decision(), self.modules)
        street = self.state.street.value
        self.apply(action, 'opponent')
        return self.event('opponent_action', seat=seat, street=street,
                          action=self.modules.trace.action_payload(action))

    def settlement(self):
        settled = self.state.settle(self.strengths)
        return dict(payouts=list(settled.payouts), final_stacks=list(settled.final_stacks),
                    pots=[dict(amount=p.amount, seats=list(p.eligible_seats))
                          for p in settled.side_pots])


class Failures:
    def __init__(self):
        self.lock, self.items = threading.Lock(), []

    def add(self, code):
        with self.lock:
            if code not in self.items:
                self.items.append(code)

    def check(self):
        with self.lock:
            if self.items:
                raise HostRefusal(self.items[0])


class Job:
    """Own a kill-on-close native job, optionally with a whole-job memory limit."""
    def __init__(self, memory_limit=None):
        class Limits(ctypes.Structure):
            _fields_ = [('process_time', ctypes.c_longlong), ('job_time', ctypes.c_longlong),
                        ('flags', ctypes.c_ulong), ('minimum', ctypes.c_size_t),
                        ('maximum', ctypes.c_size_t), ('active_limit', ctypes.c_ulong),
                        ('affinity', ctypes.c_size_t), ('priority', ctypes.c_ulong),
                        ('scheduling', ctypes.c_ulong)]
        class Extended(ctypes.Structure):
            _fields_ = [('basic', Limits), ('io', ctypes.c_ulonglong * 6),
                        ('memory', ctypes.c_size_t * 4)]
        self.api = ctypes.WinDLL('kernel32', use_last_error=True)
        signatures = {
            'CreateJobObjectW': ([ctypes.c_void_p, ctypes.c_wchar_p], ctypes.c_void_p),
            'SetInformationJobObject': ([ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p,
                                         ctypes.c_ulong], ctypes.c_int),
            'AssignProcessToJobObject': ([ctypes.c_void_p, ctypes.c_void_p], ctypes.c_int),
            'QueryInformationJobObject': ([ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p,
                                           ctypes.c_ulong, ctypes.c_void_p], ctypes.c_int),
            'TerminateJobObject': ([ctypes.c_void_p, ctypes.c_uint], ctypes.c_int),
            'CloseHandle': ([ctypes.c_void_p], ctypes.c_int),
            'CreateToolhelp32Snapshot': ([ctypes.c_ulong, ctypes.c_ulong], ctypes.c_void_p),
            'Thread32First': ([ctypes.c_void_p, ctypes.c_void_p], ctypes.c_int),
            'Thread32Next': ([ctypes.c_void_p, ctypes.c_void_p], ctypes.c_int),
            'OpenThread': ([ctypes.c_ulong, ctypes.c_int, ctypes.c_ulong], ctypes.c_void_p),
            'GetProcessIdOfThread': ([ctypes.c_void_p], ctypes.c_ulong),
            'ResumeThread': ([ctypes.c_void_p], ctypes.c_ulong),
        }
        for name, (args, result) in signatures.items():
            function = getattr(self.api, name)
            function.argtypes, function.restype = args, result
        self.handle = self.api.CreateJobObjectW(None, None)
        require(self.handle, 'containment_failed')
        limits = Extended()
        limits.basic.flags = 0x2000
        if memory_limit is not None:
            limits.basic.flags |= 0x200
            limits.memory[1] = memory_limit
        self.limits_type = Extended
        try:
            require(self.api.SetInformationJobObject(self.handle, 9, ctypes.byref(limits),
                    ctypes.sizeof(limits)), 'containment_failed')
        except BaseException as error:
            secondary = ()
            try:
                self.close()
            except BaseException:
                secondary = ('cleanup_failed',)
            raise HostRefusal('containment_failed', secondary=secondary) from error

    def peak_memory(self):
        limits = self.limits_type()
        require(self.api.QueryInformationJobObject(self.handle, 9, ctypes.byref(limits),
                ctypes.sizeof(limits), None), 'memory_sample_failed')
        return limits.memory[3]

    def assign(self, process):
        require(self.api.AssignProcessToJobObject(self.handle, int(process._handle)),
                'containment_failed')

    def resume(self, process):
        """Release the assigned redirector before it can create any interpreter child."""
        class ThreadEntry(ctypes.Structure):
            _fields_ = [('size', ctypes.c_ulong), ('usage', ctypes.c_ulong),
                        ('thread_id', ctypes.c_ulong), ('process_id', ctypes.c_ulong),
                        ('base_priority', ctypes.c_long), ('delta_priority', ctypes.c_long),
                        ('flags', ctypes.c_ulong)]
        snapshot, thread, cause, cleanup_failed = None, None, None, False
        try:
            handle = self.api.CreateToolhelp32Snapshot(4, 0)
            require(handle not in (None, ctypes.c_void_p(-1).value), 'containment_failed')
            snapshot = handle
            entry, identities = ThreadEntry(), []
            entry.size = ctypes.sizeof(entry)
            more = self.api.Thread32First(snapshot, ctypes.byref(entry))
            limit = time.monotonic() + 5
            while more:
                require(time.monotonic() < limit and entry.size >= 16, 'containment_failed')
                if entry.process_id == process.pid:
                    identities.append(entry.thread_id)
                entry.size = ctypes.sizeof(entry)
                more = self.api.Thread32Next(snapshot, ctypes.byref(entry))
            require(ctypes.get_last_error() == 18 and len(identities) == 1
                    and process.poll() is None, 'containment_failed')
            thread = self.api.OpenThread(0x0802, False, identities[0])
            require(thread, 'containment_failed')
            require(self.api.GetProcessIdOfThread(thread) == process.pid
                    and process.poll() is None, 'containment_failed')
            require(self.api.ResumeThread(thread) == 1, 'containment_failed')
        except BaseException as error:
            cause = error
        finally:
            for handle in (thread, snapshot):
                if handle:
                    try:
                        require(self.api.CloseHandle(handle), 'cleanup_failed')
                    except BaseException:
                        cleanup_failed = True
        if cause is not None:
            raise HostRefusal('containment_failed',
                              secondary=('cleanup_failed',) if cleanup_failed else ()) from cause
        require(not cleanup_failed, 'cleanup_failed')

    def active(self):
        class Accounting(ctypes.Structure):
            _fields_ = [('times', ctypes.c_longlong * 4), ('faults', ctypes.c_ulong),
                        ('total', ctypes.c_ulong), ('active', ctypes.c_ulong),
                        ('terminated', ctypes.c_ulong)]
        value = Accounting()
        require(self.api.QueryInformationJobObject(self.handle, 1, ctypes.byref(value),
                ctypes.sizeof(value), None), 'cleanup_failed')
        return value.active

    def terminate(self):
        require(self.api.TerminateJobObject(self.handle, 1), 'cleanup_failed')

    def close(self):
        if self.handle:
            handle, self.handle = self.handle, None
            require(self.api.CloseHandle(handle), 'cleanup_failed')


BOOTSTRAP = (
    "import os,sys; gate=os.read(0,1); "
    "sys.exit(91) if gate != b'G' else None; "
    "sys.path.append(os.path.join(os.path.dirname(os.path.dirname(sys.executable)),"
    "'Lib','site-packages')); "
    "import runpy; sys.argv=sys.argv[1:]; runpy.run_path(sys.argv[0],run_name='__main__')"
)


class ChildConnection:
    """Bound all transport waits without moving game mutation into I/O workers."""
    def __init__(self, source, blueprint_path, child_id, failures, strategy='blueprint-v1'):
        self.failures, self.proc, self.job = failures, None, None
        self.frames, self.writes = queue.Queue(8), queue.Queue(1)
        self.stop, self.threads = threading.Event(), []
        self.stdout, self.stderr, self.truncated = bytearray(), bytearray(), False
        self.exit_code, self.closed = None, False
        self.hand_deadline = time.monotonic() + 300
        phase = 'containment_failed'
        try:
            self.job = Job()
            environment = {k: os.environ[k] for k in ('SystemRoot', 'WINDIR', 'SystemDrive',
                'COMSPEC', 'USERPROFILE', 'APPDATA', 'LOCALAPPDATA', 'TEMP', 'TMP')
                if k in os.environ}
            environment['PONTIUS_GIT'] = str(source.git)
            from pontius.execution import child_context, CONTEXT_ENV
            environment[CONTEXT_ENV] = child_context(source.context)
            phase = 'process_start_failed'
            self.proc = subprocess.Popen([str(source.python), '-B', '-P', '-S', '-c', BOOTSTRAP,
                str(source.repo / 'tools/v0a_event_adapter.py'), '--blueprint', str(blueprint_path),
                '--session-id', child_id, '--strategy', strategy], cwd=source.repo,
                env=environment, stdin=subprocess.PIPE,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=0, close_fds=True,
                creationflags=subprocess.CREATE_NO_WINDOW | CREATE_SUSPENDED)
            phase = 'containment_failed'
            self.job.assign(self.proc)
            self.job.resume(self.proc)
            phase = 'transport_failed'
            for function, args in ((self.read_stream, (self.proc.stdout, True)),
                                   (self.read_stream, (self.proc.stderr, False)),
                                   (self.writer, ())):
                thread = threading.Thread(target=function, args=args, daemon=True)
                self.threads.append(thread)
                thread.start()
            self.startup_deadline = self.deadline()
            self.send(b'G', self.startup_deadline)
        except BaseException as error:
            self.failures.add(error.code if isinstance(error, HostRefusal) else phase)
            if isinstance(error, HostRefusal):
                for code in error.secondary:
                    self.failures.add(code)
            self.finish(False)
            raise HostRefusal(self.failures.items[0], self) from error

    def deadline(self):
        return min(time.monotonic() + 60, self.hand_deadline)

    def remaining(self, deadline):
        self.failures.check()
        left = deadline - time.monotonic()
        require(left > 0, 'host_limit')
        return min(left, 0.05)

    def read_stream(self, stream, stdout):
        capture, cap = (self.stdout, 2097152) if stdout else (self.stderr, 65536)
        pending = bytearray()
        try:
            while True:
                chunk = stream.read(4096)
                if not chunk:
                    if stdout:
                        require(not pending, 'protocol_invalid')
                        self.frames.put_nowait(None)
                    return
                available = cap - len(capture)
                capture.extend(chunk[:available])
                if len(chunk) > available:
                    self.truncated = True
                    raise HostRefusal('transport_failed')
                if stdout:
                    pending.extend(chunk)
                    while b'\n' in pending:
                        size = pending.index(10) + 1
                        require(size <= 16384, 'protocol_invalid')
                        self.frames.put_nowait(bytes(pending[:size]))
                        del pending[:size]
                    require(len(pending) < 16384, 'protocol_invalid')
        except BaseException as error:
            self.failures.add(error.code if isinstance(error, HostRefusal) else 'transport_failed')

    def writer(self):
        while not self.stop.is_set():
            try:
                raw, done = self.writes.get(timeout=0.05)
            except queue.Empty:
                continue
            try:
                offset = 0
                while offset < len(raw):
                    count = self.proc.stdin.write(raw[offset:])
                    require(type(count) is int and count > 0, 'transport_failed')
                    offset += count
            except BaseException:
                self.failures.add('transport_failed')
            finally:
                done.set()

    def send(self, raw, deadline):
        self.remaining(deadline)
        done = threading.Event()
        try:
            self.writes.put_nowait((raw, done))
        except queue.Full as error:
            raise HostRefusal('transport_failed') from error
        while not done.wait(self.remaining(deadline)):
            pass
        self.remaining(deadline)

    def receive(self, deadline):
        while True:
            try:
                value = self.frames.get(timeout=self.remaining(deadline))
                self.remaining(deadline)
                return value
            except queue.Empty:
                pass

    def finish(self, success):
        if self.closed:
            return
        self.closed = True
        def attempt(function):
            try:
                function()
            except BaseException:
                self.failures.add('cleanup_failed')
        try:
            self.stop.set()
            if self.proc is not None:
                if not success or self.failures.items:
                    if self.job is not None:
                        attempt(self.job.terminate)
                    if self.proc.poll() is None:
                        attempt(self.proc.kill)  # Also covers an unassigned gated root.
                try:
                    self.exit_code = self.proc.wait(timeout=5)
                    if self.exit_code != 0 and success:
                        self.failures.add('child_failed')
                except BaseException:
                    self.failures.add('cleanup_failed')
                    if self.job is not None:
                        attempt(self.job.terminate)
                    attempt(self.proc.kill)
                    def reap():
                        self.exit_code = self.proc.wait(timeout=5)
                    attempt(reap)
                if self.job is not None:
                    def empty():
                        limit = time.monotonic() + 5
                        while self.job.active():
                            require(time.monotonic() < limit, 'cleanup_failed')
                            self.stop.wait(0.01) if not self.stop.is_set() else time.sleep(0.01)
                    attempt(empty)
        finally:
            if self.job is not None:
                attempt(self.job.close)
            for thread in self.threads:
                if thread.ident is not None:
                    attempt(lambda t=thread: t.join(timeout=5))
                    if thread.is_alive():
                        self.failures.add('cleanup_failed')
            if self.proc is not None:
                for stream in (self.proc.stdin, self.proc.stdout, self.proc.stderr):
                    if stream is not None:
                        attempt(stream.close)
            if self.truncated:
                self.failures.add('transport_failed')


WIRE_FIELDS = {
    'ready': 'source_commit source_manifest_sha256 blueprint_artifact_sha256 '
             'blueprint_sha256 evidentiary',
    'action': 'hand_id action_index seat street action',
    'event_result': 'event_index status decision failure',
    'hand_result': 'complete settlement rank_source evidentiary preparation_compute_seconds '
                   'post_terminal_compute_seconds interrupted_response_count accounting_complete '
                   'failure_reason secondary_failures',
    'session_result': 'status terminal_publication_compute_seconds accounting_complete '
                      'failure_reason secondary_failures accounting_scope evidentiary',
}


def finite_seconds(value):
    return type(value) is float and math.isfinite(value) and value >= 0


class WireConsumer:
    def __init__(self, connection, source, table, artifact_hash, policy_hash,
                 identity=None, blueprint=None):
        self.connection, self.source, self.table = connection, source, table
        self.artifact_hash, self.policy_hash = artifact_hash, policy_hash
        self.model = table.modules.model
        self.identity = identity
        self.protocol = 'pontius-v0a-event-interface-v2' if identity is not None else PROTOCOL
        self.reasons = {}
        if identity is not None:
            try:
                codec = table.modules.codec
                self.blueprint = codec.decode_blueprint(codec.encode_blueprint(blueprint))
            except (TypeError, ValueError) as error:
                raise HostRefusal('source_invalid') from error
            require(self.blueprint.digest == policy_hash, 'source_invalid')

    def read(self, kind, deadline):
        raw = self.connection.receive(deadline)
        require(type(raw) is bytes and raw.endswith(b'\n'), 'protocol_invalid')
        row = decode_json(raw, code='protocol_invalid', digits=640, floats=True)
        require(type(row) is dict and type(row.get('type')) is str and row['type'] in WIRE_FIELDS)
        extra = (' provider config_sha256'
                 if self.identity is not None and row['type'] == 'ready' else '')
        exact_object(row, 'protocol session_id type ' + WIRE_FIELDS[row['type']] + extra)
        require(row['protocol'] == self.protocol and row['session_id'] == self.table.child_id)
        if kind == 'action' and row['type'] == 'event_result' and row['status'] == 'failed':
            require(integer(row['event_index']) and row['event_index'] == self.table.event_index
                    and (row['decision'] is None or self.identity is not None))
            if row['decision'] is not None:
                self.decision(row['decision'], self.pending_expected, successful=False)
                require(row['decision']['delivery_status'] != 'accepted')
            self.failure(row['failure'], row['decision'] if self.identity is not None else None)
            raise HostRefusal('child_failed')
        require(row['type'] == kind)
        return row

    def action(self, value):
        exact_object(value, 'kind raise_to')
        try:
            return self.model.HandAction(**value)
        except (ValueError, TypeError) as error:
            raise HostRefusal('protocol_invalid') from error

    def timing(self, value, *, successful=True):
        exact_object(value, 'status interruption_reason wall_start_ns last_valid_observation_ns '
                     'emission_observed_ns elapsed_ns response_compute_seconds '
                     'response_uninstrumented_seconds work_cutoff_crossed deadline_crossed')
        try:
            parsed = dict(value)
            parsed['status'] = self.model.TimingStatus(parsed['status'])
            if parsed['interruption_reason'] is not None:
                parsed['interruption_reason'] = self.model.FailureCode(
                    parsed['interruption_reason'])
            result = self.model.TimingRecord(**parsed)
        except (ValueError, TypeError) as error:
            raise HostRefusal('protocol_invalid') from error
        if successful and result.status == self.model.TimingStatus.COMPLETED:
            require(result.work_cutoff_crossed is False and result.deadline_crossed is False
                    and result.elapsed_ns <= 15000000000)
            require(abs(result.response_compute_seconds + result.response_uninstrumented_seconds
                        - result.elapsed_ns / 1e9) <= 2e-9)
        return result

    def failure(self, value, decision=None):
        exact_object(value, 'hand_id event_index action_index code delivery_status '
                     'delivered_action timing')
        try:
            parsed = dict(value)
            parsed['code'] = self.model.FailureCode(parsed['code'])
            parsed['delivery_status'] = self.model.DeliveryStatus(parsed['delivery_status'])
            parsed['delivered_action'] = (None if value['delivered_action'] is None
                                          else self.action(value['delivered_action']))
            parsed['timing'] = (None if value['timing'] is None
                                else self.timing(value['timing'], successful=False))
            self.model.FailureRecord(**parsed)
        except (ValueError, TypeError) as error:
            raise HostRefusal('protocol_invalid') from error
        if decision is not None:
            require(value['code'] == decision['failure_reason']
                    and all(value[key] == decision[key] for key in (
                        'hand_id', 'event_index', 'action_index', 'delivery_status',
                        'delivered_action', 'timing')))

    def ready(self):
        row = self.read('ready', self.connection.startup_deadline)
        require(row['source_commit'] == self.source.commit
                and row['source_manifest_sha256'] == self.source.child_manifest
                and row['blueprint_artifact_sha256'] == self.artifact_hash
                and row['blueprint_sha256'] == self.policy_hash and row['evidentiary'] is False)
        if self.identity is not None:
            require(row['provider'] == self.identity.provider
                    and row['config_sha256'] == self.identity.config_sha256)

    def provider_expected(self):
        table, modules = self.table, self.table.modules
        self.context_state = table.state
        observation = modules.provider_model.DecisionObservation(
            version='pontius-decision-observation-v1', hand_id=table.child_id,
            action_index=table.bot_index + 1, cards=table.views[table.config.controlled_seat],
            betting=table.state, decision=table.state.legal_decision(), remaining_work_ns=0)
        fallback = self.blueprint.action_for(cards=observation.cards, betting=observation.betting,
                                            decision=observation.decision)
        return dict(hand_id=table.child_id, event_index=table.event_index,
            action_index=table.bot_index + 1, street_action_index=table.street_index + 1,
            seat=table.config.controlled_seat, street=table.state.street.value,
            state_before_sha256=modules.spine.public_betting_state_sha256(table.state),
            visible_cards_sha256=modules.model.visible_cards_sha256(observation.cards),
            decision_sha256=observation.decision_sha256,
            source_manifest_sha256=self.source.child_manifest, provider=self.identity.provider,
            config_sha256=self.identity.config_sha256, fallback_blueprint_sha256=self.policy_hash,
            fallback_action=modules.trace.action_payload(
                self.model.HandAction.from_betting_action(fallback.action)),
            fallback_reason='table_hit' if fallback.table_hit else 'passive_default')

    def decision(self, value, expected, *, successful=True):
        if self.identity is not None:
            try:
                self.table.modules.provider_codec.validate_decision(value)
                self.context_state.apply_action(
                    self.action(value['fallback_action']).to_betting_action())
                changed = self.context_state.apply_action(
                    self.action(value['selected_action']).to_betting_action())
            except (ValueError, TypeError) as error:
                raise HostRefusal('protocol_invalid') from error
            require(all(value[k] == v for k, v in expected.items()), 'state_mismatch')
            proposal = value['proposal']
            if proposal is not None:
                valid = proposal['decision_sha256'] == value['decision_sha256']
                if proposal['action'] is not None:
                    try:
                        self.context_state.apply_action(
                            self.action(proposal['action']).to_betting_action())
                    except (ValueError, TypeError):
                        valid = False
                require(valid == (value['provider_outcome'] in ('proposed', 'abstained')),
                        'state_mismatch')
            if value['applied_action'] is not None:
                require(value['state_after_sha256'] ==
                        self.table.modules.spine.public_betting_state_sha256(changed),
                        'state_mismatch')
            if successful:
                timing = self.timing(value['timing'])
                require(value['failure_reason'] is None
                        and timing.status == self.model.TimingStatus.COMPLETED
                        and value['delivery_status'] == 'accepted'
                        and value['delivered_action'] == value['applied_action'])
                reason = (value['proposal']['reason'] if value['selection_origin'] == 'provider'
                          else 'fallback_' + value['selection_reason'])
                self.reasons[value['action_index']] = reason
            return
        exact_object(value, 'hand_id event_index action_index street_action_index seat street '
                     'state_before_sha256 state_after_sha256 visible_cards_sha256 blueprint_sha256 '
                     'selected_action selection_reason spine_reason timing preparation_use '
                     'failure_reason')
        action, timing = self.action(value['selected_action']), self.timing(value['timing'])
        prep = exact_object(value['preparation_use'],
                            'producer_status artifact_sha256s credited_seconds')
        require(prep['producer_status'] == 'producer_absent'
                and type(prep['artifact_sha256s']) is list
                and prep['artifact_sha256s'] == [] and integer(prep['credited_seconds'], 0, 0))
        try:
            parsed = dict(value, selected_action=action, timing=timing,
                          preparation_use=self.model.PreparationUseRecord(),
                          selection_reason=self.model.SelectionReason(value['selection_reason']))
            self.model.DecisionRecord(**parsed)
        except (ValueError, TypeError) as error:
            raise HostRefusal('protocol_invalid') from error
        require(value['failure_reason'] is None
                and timing.status == self.model.TimingStatus.COMPLETED)
        require(all(value[k] == v for k, v in expected.items()), 'state_mismatch')

    def exchange(self, event):
        table, modules = self.table, self.table.modules
        deadline = self.connection.deadline()
        self.connection.send((json.dumps(event, separators=(',', ':')) + '\n').encode(), deadline)
        expected = None
        if table.expects_action():
            provider_expected = self.provider_expected() if self.identity is not None else None
            self.pending_expected = provider_expected
            row = self.read('action', deadline)
            require(integer(row['action_index'], 1) and integer(row['seat'], 0, 5)
                    and row['hand_id'] == table.child_id
                    and row['action_index'] == table.bot_index + 1
                    and row['seat'] == table.config.controlled_seat
                    and row['street'] == table.state.street.value)
            action = self.action(row['action'])
            expected = dict(hand_id=table.child_id, event_index=table.event_index,
                action_index=table.bot_index + 1, street_action_index=table.street_index + 1,
                seat=table.config.controlled_seat, street=table.state.street.value,
                state_before_sha256=modules.spine.public_betting_state_sha256(table.state),
                visible_cards_sha256=modules.model.visible_cards_sha256(
                    table.views[table.config.controlled_seat]),
                blueprint_sha256=self.policy_hash, selected_action=row['action'])
            if provider_expected is not None:
                expected = dict(provider_expected, selected_action=row['action'],
                                applied_action=row['action'])
            table.apply_bot(action)
            expected['state_after_sha256'] = modules.spine.public_betting_state_sha256(table.state)
        row = self.read('event_result', deadline)
        require(integer(row['event_index']) and row['event_index'] == table.event_index
                and type(row['status']) is str
                and row['status'] in ('accepted', 'decided', 'failed'))
        if row['status'] == 'failed':
            require(row['decision'] is None or self.identity is not None)
            if row['decision'] is not None:
                require(expected is not None)
                self.decision(row['decision'], expected, successful=False)
            self.failure(row['failure'], row['decision'] if self.identity is not None else None)
            raise HostRefusal('child_failed')
        require(row['failure'] is None)
        if expected is None:
            require(row['status'] == 'accepted' and row['decision'] is None)
        else:
            require(row['status'] == 'decided')
            self.decision(row['decision'], expected)

    def closure_fields(self, row):
        require(type(row['accounting_complete']) is bool and row['evidentiary'] is False
                and type(row['secondary_failures']) is list)
        causes = row['secondary_failures']
        require(all(type(v) is str and v in tuple(self.model.FailureCode) for v in causes)
                and len(set(causes)) == len(causes))
        primary = row['failure_reason']
        require(primary is None or type(primary) is str
                and primary in tuple(self.model.FailureCode))
        require(primary not in causes and (primary is not None or not causes))

    def settlement(self, value):
        exact_object(value, 'payouts final_stacks pots')
        for key in ('payouts', 'final_stacks'):
            require(type(value[key]) is list and len(value[key]) == 6
                    and all(integer(v, 0, 1000000) for v in value[key]))
        require(type(value['pots']) is list and len(value['pots']) <= 6)
        for pot in value['pots']:
            exact_object(pot, 'amount seats')
            require(integer(pot['amount'], 1, 1000000) and type(pot['seats']) is list
                    and 0 < len(pot['seats']) <= 6 and all(integer(s, 0, 5) for s in pot['seats'])
                    and pot['seats'] == sorted(set(pot['seats'])))
        require(value == self.table.settlement(), 'settlement_mismatch')

    def complete(self):
        deadline = self.connection.deadline()
        hand = self.read('hand_result', deadline)
        self.closure_fields(hand)
        require(type(hand['complete']) is bool and integer(hand['interrupted_response_count']))
        for key in ('preparation_compute_seconds', 'post_terminal_compute_seconds'):
            require(finite_seconds(hand[key]))
        require(hand['rank_source'] in (None, 'not_required', 'host_supplied'))
        if not hand['complete']:
            require(hand['settlement'] is None and hand['rank_source'] is None)
            raise HostRefusal('child_failed')
        require(hand['accounting_complete'] and hand['interrupted_response_count'] == 0
                and hand['failure_reason'] is None and not hand['secondary_failures'])
        require(hand['rank_source'] == ('host_supplied' if self.table.showdown_sent
                                       else 'not_required'))
        self.settlement(hand['settlement'])
        closing = self.read('session_result', deadline)
        self.closure_fields(closing)
        require(closing['status'] in ('completed', 'failed')
                and closing['accounting_scope'] == 'runtime_begin_to_final_publication')
        duration = closing['terminal_publication_compute_seconds']
        require(duration is None or finite_seconds(duration))
        if closing['status'] == 'failed':
            raise HostRefusal('child_failed')
        require(closing['accounting_complete'] and finite_seconds(duration)
                and closing['failure_reason'] is None and not closing['secondary_failures'])
        require(self.connection.receive(deadline) is None)
        return hand['settlement']


def main(argv=None):
    started = time.perf_counter()
    source = None
    failures = Failures()
    report = dict(version='pontius-v0a-table-result-v1', session_id=None, status='failed',
        failure_reason=None, secondary_failures=[], input_sha256=None,
        blueprint_artifact_sha256=None,
        blueprint_sha256=None, source_commit=None, applied_actions=[], settlement=None,
        child_exit_code=None, child_stdout_base64='', child_stderr_base64='',
        capture_truncated=False)
    connection, table, provisional = None, None, None
    phase = 'input_invalid'
    try:
        parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False, add_help=False)
        for flag in ('table', 'blueprint', 'session-id'):
            parser.add_argument('--' + flag, required=True)
        parser.add_argument('--strategy', choices=('blueprint-v1', 'baseline-rules-v1'),
                            default='blueprint-v1')
        parser.add_argument('--reviewed-commit')
        parser.add_argument('--development', action='store_true')
        args = parser.parse_args(argv)
        baseline = args.strategy == 'baseline-rules-v1'
        prefix = 'pontius-v0a-table-host-v2-correctness-' if baseline else PREFIX
        protocol = 'pontius-v0a-event-interface-v2' if baseline else PROTOCOL
        if baseline:
            report.update(version='pontius-v0a-table-result-v2', provider=None, config_sha256=None)
        report['session_id'] = args.session_id
        require(re.fullmatch(re.escape(prefix) + '[A-Za-z0-9_-]{1,48}', args.session_id),
                'input_invalid')
        child_id = protocol + '-correctness-table-' + args.session_id[len(prefix):]
        phase = 'source_invalid'
        source = Source(Path.cwd(), reviewed_commit=args.reviewed_commit,
                        development=args.development)
        report['source_commit'] = source.commit
        phase = 'input_invalid'
        table_input, blueprint_input = OwnedInput(Path(args.table), 16384), OwnedInput(
            Path(args.blueprint), 1048576)
        report['input_sha256'] = hashlib.sha256(table_input.raw).hexdigest()
        report['blueprint_artifact_sha256'] = hashlib.sha256(blueprint_input.raw).hexdigest()
        phase = 'source_invalid'
        modules = source.load()
        phase = 'input_invalid'
        config = TableInput.decode(table_input.raw, modules)
        blueprint = modules.codec.decode_blueprint(blueprint_input.raw)
        report['blueprint_sha256'] = blueprint.digest
        identity = (modules.providers.make_provider(args.strategy, blueprint).identity
                    if baseline else None)
        if baseline:
            report.update(provider=identity.provider, config_sha256=identity.config_sha256)
        table = Table(config, modules, child_id)
        phase = 'process_start_failed'
        connection = ChildConnection(source, blueprint_input.path, child_id,
                                     failures, args.strategy)
        consumer = WireConsumer(connection, source, table, report['blueprint_artifact_sha256'],
                                report['blueprint_sha256'], identity,
                                blueprint if baseline else None)
        phase = 'protocol_invalid'
        consumer.ready()
        event = table.start_event()
        while event is not None:
            consumer.exchange(event)
            event = table.next_event()
        provisional = consumer.complete()
    except BaseException as error:
        if isinstance(error, HostRefusal) and error.connection is not None:
            connection = error.connection
        failures.add(error.code if isinstance(error, HostRefusal) else phase)
    finally:
        if connection is not None:
            connection.finish(provisional is not None and not failures.items)
            report.update(child_exit_code=connection.exit_code,
                child_stdout_base64=base64.b64encode(connection.stdout).decode('ascii'),
                child_stderr_base64=base64.b64encode(connection.stderr).decode('ascii'),
                capture_truncated=connection.truncated)
        if table is not None:
            report['applied_actions'] = table.applied_actions
    if not failures.items and provisional is not None:
        report.update(status='completed', settlement=provisional)
    report.update(failure_reason=failures.items[0] if failures.items else None,
                  secondary_failures=failures.items[1:])
    if source is not None:
        from pontius.execution import finish_run
        finish_run(source.context, 'v0a_table_host', report, time.perf_counter() - started)
    try:
        raw = (json.dumps(report, sort_keys=True, separators=(',', ':'), allow_nan=False)
               + '\n').encode('utf-8')
        require(os.write(sys.stdout.fileno(), raw) == len(raw), 'output_failed')
    except BaseException:
        try:
            os.write(sys.stderr.fileno(), b'REFUSED output_failed\n')
        except BaseException:
            pass
        return 1
    return 0 if report['status'] == 'completed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
