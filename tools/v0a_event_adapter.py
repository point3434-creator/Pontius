"""One-hand correctness event pipe; local byte receipts, no operating authority."""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import msvcrt
import os
from pathlib import Path
import re
import stat
import subprocess
import sys

BASE = '5f90279ab3d7d78fe790b115a697c52262280c0d'
TOOLS = ('tools/v0a_event_adapter.py', 'tools/v0a_hand_adapter.py',
         'tools/v0a_rehearsal_driver.py')
PROTOCOL = 'pontius-v0a-event-interface-v1'
PREFIX = PROTOCOL + '-correctness-'
FRAME_LIMIT = 16384


class AdapterRefusal(ValueError):
    """An admission or byte-delivery refusal; no retry repairs retained output."""


def require(condition, reason):
    if not condition:
        raise AdapterRefusal(reason)


def regular(path, directory=False):
    info = path.lstat()
    require(not info.st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT
            and (stat.S_ISDIR(info.st_mode) if directory else stat.S_ISREG(info.st_mode)),
            'PATH: require regular non-reparse source')


def checked_path(path, *, directory=False, d_local=True):
    require(path.is_absolute() and len(path.drive) == 2 and '..' not in path.parts
            and (not d_local or path.drive.upper() == 'D:'), 'PATH: absolute local path required')
    for parent in path.parents:
        regular(parent, directory=True)
    regular(path, directory)
    return path


class Source:
    """Raw commit/blob binding; bootstrap precedes the declared runtime accounting."""
    def __init__(self, repo):
        require(os.name == 'nt' and sys.flags.dont_write_bytecode and sys.flags.safe_path,
                'SOURCE: require Windows Python -B -P')
        require(not any(n == 'pontius' or n.startswith('pontius.') for n in sys.modules),
                'SOURCE: pontius must not be preloaded')
        self.repo = checked_path(repo, directory=True)
        require(Path(__file__).absolute() == self.repo / TOOLS[0],
                'SOURCE: executed tool origin differs')
        self.git = checked_path(Path(os.environ.get('PONTIUS_GIT', '')), d_local=False)
        self.env = {k: v for k, v in os.environ.items()
                    if not k.upper().startswith(('GIT_', 'PYTHON', 'PONTIUS_'))}
        self.commit = self.head()
        current, inherited = self.inventory(self.commit), self.inventory(BASE)
        require(set(current) == set(inherited) | {TOOLS[0]},
                'SOURCE: unexpected committed source population')
        require(all(current[p] == oid for p, oid in inherited.items()),
                'SOURCE: inherited source differs from pinned base')
        stream = io.BytesIO(self.command('cat-file', '--batch',
                            content=('\n'.join(current.values()) + '\n').encode('ascii')))
        self.expected = {}
        for path, oid in current.items():
            header = stream.readline().split()
            require(len(header) == 3 and header[:2] == [oid.encode(), b'blob'],
                    'SOURCE: unexpected raw object')
            content = stream.read(int(header[2]))
            require(len(content) == int(header[2]) and stream.read(1) == b'\n',
                    'SOURCE: truncated raw blob')
            self.expected[path] = content
        require(stream.read() == b'', 'SOURCE: extra raw object output')
        rows = sorted(hashlib.sha256(raw).hexdigest().encode() + b'  ' + path.encode() + b'\n'
                      for path, raw in self.expected.items())
        self.manifest = hashlib.sha256(b''.join(rows)).hexdigest()
        self.check()

    def command(self, *args, content=None):
        result = subprocess.run([str(self.git), '--no-replace-objects', '--no-optional-locks',
                                 '-C', str(self.repo), *args], input=content, env=self.env,
                                capture_output=True, timeout=30)
        require(result.returncode == 0, 'SOURCE: raw Git operation failed')
        return result.stdout

    def head(self):
        commit = self.command('rev-parse', '--verify', 'HEAD^{commit}').decode('ascii').strip()
        require(re.fullmatch('[0-9a-f]{40}', commit), 'SOURCE: invalid commit identity')
        return commit

    def inventory(self, commit):
        entries = self.command('ls-tree', '-r', '-z', commit, '--', 'src/pontius', *TOOLS)
        result = {}
        for row in entries.split(b'\0'):
            if not row:
                continue
            metadata, name = row.split(b'\t', 1)
            mode, kind, oid = metadata.split()
            require(mode in (b'100644', b'100755') and kind == b'blob',
                    'SOURCE: committed source must be regular blobs')
            result[name.decode('utf-8')] = oid.decode('ascii')
        require(result, 'SOURCE: empty raw source inventory')
        return result

    def check(self):
        require(self.head() == self.commit, 'SOURCE: HEAD changed during invocation')
        package = checked_path(self.repo / 'src/pontius', directory=True)
        actual, directories = {}, set()
        for parent, dirs, files in os.walk(package, followlinks=False):
            for name in dirs:
                path = Path(parent) / name
                regular(path, directory=True)
                directories.add(path.relative_to(self.repo).as_posix())
            for name in files:
                path = Path(parent) / name
                regular(path)
                actual[path.relative_to(self.repo).as_posix()] = path.read_bytes()
        expected_dirs = {p.as_posix() for name in self.expected
                         if name.startswith('src/pontius/') for p in Path(name).parents
                         if p.as_posix().startswith('src/pontius/')}
        require(directories == expected_dirs, 'SOURCE: extra or missing package directory')
        for name in TOOLS:
            actual[name] = checked_path(self.repo / name).read_bytes()
        require(actual == self.expected, 'SOURCE: missing, changed, extra or cached source')

    def load(self):
        sys.path.insert(0, str(self.repo / 'src'))
        import pontius.blueprint_artifact.codec as codec
        import pontius.v0a.model as model
        import pontius.v0a.runtime as core
        import pontius.v0a.clock as clock
        import pontius.v0a.trace as trace
        for name, module in tuple(sys.modules.items()):
            if name == 'pontius' or name.startswith('pontius.'):
                relative = 'src/' + name.replace('.', '/')
                origin = Path(module.__file__).absolute()
                require(any(origin == self.repo / path and path in self.expected
                            for path in (relative + '.py', relative + '/__init__.py')),
                        'SOURCE: delayed import origin differs')
        return codec, model, core, clock, trace


def reject_number(token):
    raise AdapterRefusal('EVENT: non-integer number')


def parse_integer(token):
    require(len(token.lstrip('-')) <= 640, 'EVENT: integer exceeds decimal domain')
    return int(token)


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, 'EVENT: duplicate member')
        result[key] = value
    return result


def array(value):
    require(type(value) is list, 'EVENT: expected array')
    return tuple(value)


def decode_frame(raw, session_id, model):
    """Decode only after the inherited response boundary has opened."""
    require(type(raw) is bytes and 0 < len(raw) <= FRAME_LIMIT and raw.endswith(b'\n'),
            'EVENT: incomplete or oversized frame')
    require(b'\r' not in raw and not raw.startswith(b'\xef\xbb\xbf'),
            'EVENT: CR/BOM is not admitted')
    value = json.loads(raw.decode('utf-8'), object_pairs_hook=unique_object,
                       parse_int=parse_integer, parse_float=reject_number,
                       parse_constant=reject_number)
    require(type(value) is dict and type(value.get('kind')) is str,
            'EVENT: expected named object')
    kind = value.pop('kind')
    common = {'schema_version', 'hand_id', 'event_index'}
    fields = {
        'hand_started': {'button', 'controlled_seat', 'starting_stacks', 'small_blind',
                         'big_blind', 'private_cards'},
        'opponent_action': {'street', 'seat', 'action'},
        'street_revealed': {'street', 'cards'},
        'showdown_result': {'strengths'},
    }
    require(kind in fields and set(value) == common | fields[kind], 'EVENT: member set differs')
    require(value['hand_id'] == session_id, 'EVENT: session identity differs')
    if kind == 'hand_started':
        value['starting_stacks'] = array(value['starting_stacks'])
        value['private_cards'] = array(value['private_cards'])
        admitted = model.HandStartedEvent(**value)
        require(sum(admitted.starting_stacks) < 10**640, 'EVENT: chip total exceeds domain')
    elif kind == 'opponent_action':
        action = value['action']
        require(type(action) is dict and set(action) == {'kind', 'raise_to'},
                'EVENT: action member set differs')
        value['action'] = model.HandAction(**action)
        admitted = model.OpponentActionEvent(**value)
    elif kind == 'street_revealed':
        value['cards'] = array(value['cards'])
        admitted = model.StreetRevealedEvent(**value)
    else:
        value['strengths'] = tuple(array(rank) if type(rank) is list else rank
                                   for rank in array(value['strengths']))
        admitted = model.ShowdownResultEvent(**value)
    return model.admit_event(admitted)


def runtime_type(model, core, clock):
    """Pinned runtime dispatch shell; game/selection/emission logic stays inherited."""
    class FrameRuntime(core.HandRuntime):
        def __init__(self, *, session_id, **kwargs):
            super().__init__(**kwargs)
            self.session_id = session_id
            self.event_index = None

        def dispatch_frame(self, raw):
            self.event_index = None
            if self._dead or self._complete:
                return self._reject(model.FailureCode.EVENT_ORDER)
            if self._outer is None:
                try:
                    self._outer = core.ActionClockLedger('preflop', clock_ns=self._witness)
                except (clock.ClockInvalidError, clock.ClockReversedError) as error:
                    return self._clock_reject(error, wall_start_ns=None)
            try:
                boundary = self._outer.start_transition_boundary()
            except (clock.ClockInvalidError, clock.ClockReversedError) as error:
                return self._clock_reject(error, wall_start_ns=None)
            except RuntimeError:
                return self._reject(model.FailureCode.EVENT_ORDER)
            wall_start_ns = boundary.started_ns
            terminal_at_entry = self.betting_terminal
            self._boundary_open = True
            self._known_cutoff = None
            self._known_deadline = None
            admitted = None
            try:
                try:
                    admitted = decode_frame(raw, self.session_id, model)
                except (TypeError, ValueError, RecursionError):
                    raise core._HandFailure(model.FailureCode.INVALID_EVENT) from None
                self.event_index = admitted.event_index
                return self._process(admitted, boundary, wall_start_ns, terminal_at_entry)
            except core._HandFailure as failure:
                if failure.clock_error is None:
                    self.record(failure.code)
                else:
                    self._retain_error(failure.clock_error, otherwise=failure.code)
                self._release_boundary(boundary, terminal_at_entry)
                return self._from_failure(failure, admitted)
    return FrameRuntime


class PipeOutput:
    """A full-count local write is a receipt, not a consumer-application acknowledgement."""
    def __init__(self, session_id, model, trace, descriptor):
        self.session_id, self.model, self.trace = session_id, model, trace
        self.descriptor = descriptor
        self.identities = set()

    def frame(self, kind, **fields):
        value = dict(protocol=PROTOCOL, session_id=self.session_id, type=kind, **fields)
        raw = (json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)
               + '\n').encode('utf-8')
        require(os.write(self.descriptor, raw) == len(raw), 'OUTPUT: incomplete frame write')

    def deliver(self, envelope):
        identity = envelope.hand_id, envelope.action_index
        if identity in self.identities:
            raise self.model.MailboxRejectionError('duplicate action identity')
        self.identities.add(identity)
        self.frame('action', hand_id=envelope.hand_id, action_index=envelope.action_index,
                   seat=envelope.seat, street=envelope.street,
                   action=self.trace.action_payload(envelope.action))
        return self.model.DeliveryReceipt(*identity)


def failures(codes):
    return dict(failure_reason=codes[0].value if codes else None,
                secondary_failures=[code.value for code in codes[1:]])


def refuse(reason):
    try:
        os.write(sys.stderr.fileno(), ('REFUSED ' + reason + '\n').encode('ascii'))
    except BaseException:
        pass
    return 1


def run_session(runtime, output, source, artifact_hash, core, trace, model):
    """Required host intervals, pre-publication cut, then a separate closing receipt."""
    codes = model.FailureCode
    settlement = None
    try:
        runtime.begin_host_accounting()
        with runtime.owned_bookkeeping(body_failure=codes.TRACE_WRITE_FAILED, required=True):
            output.frame('ready', source_commit=source.commit,
                         source_manifest_sha256=source.manifest,
                         blueprint_artifact_sha256=artifact_hash,
                         blueprint_sha256=runtime.blueprint_sha256, evidentiary=False)
        while not runtime.hand_complete:
            try:
                raw = sys.stdin.buffer.readline(FRAME_LIMIT + 1)
            except (OSError, ValueError):
                runtime.record(codes.INVALID_EVENT)
                break
            outcome = runtime.dispatch_frame(raw)
            with runtime.owned_bookkeeping(body_failure=codes.TRACE_WRITE_FAILED, required=True):
                output.frame('event_result', event_index=runtime.event_index, status=outcome.status,
                             decision=None if outcome.decision is None else
                             trace.decision_payload(outcome.decision),
                             failure=None if outcome.failure is None else
                             trace.failure_payload(outcome.failure))
            if outcome.status == 'failed':
                break
        if runtime.hand_complete and not runtime.closure_failures:
            with runtime.owned_bookkeeping(body_failure=codes.SETTLEMENT_MISMATCH, required=True):
                settlement = runtime.settle()
            with runtime.owned_bookkeeping(body_failure=codes.SOURCE_BINDING_MISMATCH,
                                           required=True):
                source.check()
    except core.OperationFailed:
        pass  # The public owner has already retained the actual cause and cleanup faults.
    totals, causes = runtime.accounting(), runtime.closure_failures
    cut_success = (runtime.hand_complete and settlement is not None
                   and totals.complete and not causes)
    publication, published = [], False
    if runtime.measurable:
        try:
            with runtime.owned_publication(publication, body_failure=codes.TRACE_WRITE_FAILED):
                if runtime.measurable:
                    rank_source = None
                    if cut_success:
                        rank_source = ('host_supplied' if runtime.state.terminal_reason.value
                                       == 'showdown' else 'not_required')
                    output.frame('hand_result', complete=cut_success, rank_source=rank_source,
                                 settlement=(trace.settlement_payload(settlement)
                                             if cut_success else None),
                                 preparation_compute_seconds=totals.preparation_compute_seconds,
                                 post_terminal_compute_seconds=totals.post_terminal_compute_seconds,
                                 interrupted_response_count=totals.interrupted_response_count,
                                 accounting_complete=totals.complete, evidentiary=False,
                                 **failures(causes))
                    published = True
        except core.OperationFailed:
            pass
    runtime.finalize_accounting()
    final_totals, causes = runtime.accounting(), runtime.closure_failures
    duration = publication[0] if len(publication) == 1 else None
    valid_duration = type(duration) is float and 0 <= duration < float('inf')
    completed = bool(cut_success and published and valid_duration and final_totals.complete
                     and not causes)
    try:
        output.frame('session_result', status='completed' if completed else 'failed',
                     terminal_publication_compute_seconds=duration if valid_duration else None,
                     accounting_complete=final_totals.complete, **failures(causes),
                     accounting_scope='runtime_begin_to_final_publication', evidentiary=False)
    except BaseException:
        runtime.record(codes.TRACE_WRITE_FAILED)
        completed = False
    if completed:
        return 0
    causes = runtime.closure_failures
    return refuse(causes[0].value if causes else 'incomplete_accounting')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument('--blueprint', required=True)
    parser.add_argument('--session-id', required=True)
    try:
        args = parser.parse_args(argv)
        require(re.fullmatch(re.escape(PREFIX) + '[A-Za-z0-9_-]{1,64}', args.session_id),
                'IDENTITY: invalid correctness session')
        source = Source(Path.cwd())
        raw = checked_path(Path(args.blueprint)).read_bytes()
        codec, model, core, clock, trace = source.load()
        blueprint = codec.decode_blueprint(raw)
        msvcrt.setmode(sys.stdin.fileno(), os.O_BINARY)
        msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)
        output = PipeOutput(args.session_id, model, trace, sys.stdout.fileno())
        runtime = runtime_type(model, core, clock)(session_id=args.session_id,
                                                   blueprint=blueprint, mailbox=output)
        return run_session(runtime, output, source, hashlib.sha256(raw).hexdigest(),
                           core, trace, model)
    except BaseException as error:
        return refuse(type(error).__name__)


if __name__ == '__main__':
    raise SystemExit(main())
