"""Bounded controller for the sealed representative-blueprint workload."""
from __future__ import annotations

import argparse
import base64
import ctypes
import hashlib
import io
import json
import msvcrt
import os
from pathlib import Path
import queue
import re
import stat
import subprocess
import sys
import threading
import time
import types

BASE = '7242891bc8020d33737c3a027ef88d1b65bb2ace'
VERSION = 'workload-r002'
FILE_LIMIT = 128 * 1024 * 1024
AUTHORITY = 'docs/architecture/v0a-blueprint-workload-r001/invocation-authority.json'
PROTOCOL = 'docs/architecture/v0a-blueprint-workload-r001/execution-protocol.md'
EXCEPTIONS = ('tools/check_stabilization_boundaries.py', 'tools/generate_test_inventory.py',
              'tests/test-inventory.json', 'tests/test-profiles.toml',
              'tests/test_inventory_and_profiles.py', '.github/workflows/ci.yml')
ADDITIONS = tuple('tools/v0a_blueprint_workload' + suffix + '.py'
                  for suffix in ('', '_population', '_measure', '_report')) + tuple(
    'tests/test_blueprint_workload_' + name + '.py'
    for name in ('population', 'measure', 'session', 'report')) + (
    'tests/fixtures/blueprint_workload/control.json',)
TOOLS = {
    'host': ('tools/v0a_table_host.py', '7beb178989b3ff98b684093ce4022667a1c61ece'),
    'session': ('tools/v0a_table_session.py', '5b0608b74e46a5366d3412a11aa06c850110960e'),
    'population': ('tools/v0a_blueprint_workload_population.py', None),
    'measure': ('tools/v0a_blueprint_workload_measure.py', None),
    'report': ('tools/v0a_blueprint_workload_report.py', None),
}
POINTS = {
    'session': ('Admission.__init__ Admission.check Schedule.derive Session.prepare '
                'Session.validate Session.play_hand Session.run').split(),
    'host': ('Source.__init__ Source.check OwnedInput.check ChildConnection.__init__ '
             'ChildConnection.send ChildConnection.receive ChildConnection.finish '
             'WireConsumer.ready WireConsumer.provider_expected WireConsumer.decision '
             'WireConsumer.settlement WireConsumer.exchange WireConsumer.complete '
             'Table.start_event Table.next_event').split(),
}


class Refusal(ValueError):
    def __init__(self, code, *, secondary=()):
        super().__init__(code)
        self.code, self.secondary = code, tuple(secondary)


def require(condition, code='input_invalid'):
    if not condition:
        raise Refusal(code)


def encode(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)
            + '\n').encode('utf-8')


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def regular(path, *, directory=False):
    require(type(path) is type(Path()) and path.is_absolute() and '..' not in path.parts)
    identities = []
    for current in reversed((path, *path.parents)):
        info = current.lstat()
        require(not info.st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT
                and (stat.S_ISDIR(info.st_mode) if current != path or directory
                     else stat.S_ISREG(info.st_mode)))
        identities.append((str(current), info.st_dev, info.st_ino))
    return tuple(identities)


def file_identity(stream):
    # FileIdInfo avoids the CPython <=3.11 stat volume-serial truncation boundary.
    class Identity(ctypes.Structure):
        _fields_ = [('volume', ctypes.c_ulonglong), ('id', ctypes.c_ubyte * 16)]
    api = ctypes.WinDLL('kernel32', use_last_error=True)
    function = api.GetFileInformationByHandleEx
    function.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p, ctypes.c_ulong]
    function.restype = ctypes.c_int
    result = Identity()
    require(function(msvcrt.get_osfhandle(stream.fileno()), 18, ctypes.byref(result),
                     ctypes.sizeof(result)))
    return result.volume, bytes(result.id)


class OwnedFile:
    """Retain raw bytes and a real handle; check path, ancestors and held object."""
    def __init__(self, path, limit=FILE_LIMIT, code='input_invalid'):
        self.path, self.limit, self.code, self.stream = path, limit, code, None
        try:
            require(type(limit) is int and 0 < limit <= FILE_LIMIT)
            self.ancestors = regular(path)
            self.stream = path.open('rb')
            self.identity = file_identity(self.stream)
            self.raw = self.stream.read(limit + 1)
            require(len(self.raw) <= limit)
            self.check()
        except (OSError, ValueError) as error:
            self.close()
            raise Refusal(code) from error

    def check(self):
        try:
            require(regular(self.path) == self.ancestors)
            with self.path.open('rb') as probe:
                require(file_identity(probe) == self.identity
                        and probe.read(self.limit + 1) == self.raw)
            self.stream.seek(0)
            require(file_identity(self.stream) == self.identity
                    and self.stream.read(self.limit + 1) == self.raw)
            require(regular(self.path) == self.ancestors)
        except (OSError, ValueError) as error:
            raise Refusal(self.code) from error

    def close(self):
        if self.stream is not None:
            self.stream.close()
            self.stream = None

    def __enter__(self):
        return self

    def __exit__(self, *unused):
        self.close()


class Writer:
    def __init__(self, root, limit=FILE_LIMIT):
        regular(root, directory=True)
        self.root, self.limit, self.references = root, limit, []

    def __call__(self, relative, raw):
        require(type(relative) is str and type(raw) is bytes
                and relative and '\\' not in relative and ':' not in relative
                and all(p not in ('', '.', '..') for p in relative.split('/')))
        require(len(raw) <= self.limit, 'capture_limit')
        target = self.root / relative
        require(not target.is_absolute() or target.is_relative_to(self.root))
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            regular(target.parent, directory=True)
            with target.open('xb') as output:
                output.write(raw)
                output.flush()
                os.fsync(output.fileno())
        except OSError as error:
            raise Refusal('input_invalid') from error
        reference = {'path': relative, 'sha256': digest(raw), 'bytes': len(raw)}
        self.references.append(reference)
        return reference


def load_tool(name, root=None, captured=None):
    require(name in TOOLS, 'source_invalid')
    root = Path(__file__).absolute().parents[1] if root is None else root
    relative, oid = TOOLS[name]
    if captured is None:
        with OwnedFile(root / relative, code='source_invalid') as owned:
            raw = owned.raw
    else:
        raw = captured[relative]
    require(oid is None or hashlib.sha1(
        b'blob ' + str(len(raw)).encode('ascii') + b'\0' + raw).hexdigest() == oid,
        'source_invalid')
    alias = 'pontius_workload_' + name
    module = types.ModuleType(alias)
    module.__file__, module.__package__ = str(root / relative), ''
    sys.modules[alias] = module
    exec(compile(raw, module.__file__, 'exec'), module.__dict__)
    return module


class FrozenSource:
    """Bind the entire executed raw tree and preserve the prospectively protected B census."""
    def __init__(self, root):
        self.root, self.owned = root, {}
        try:
            require(root.drive.upper() == 'D:' and regular(root, directory=True),
                    'source_invalid')
            git_path = Path(os.environ.get('PONTIUS_GIT', ''))
            require(git_path == Path(r'C:\Program Files\Git\cmd\git.exe'), 'source_invalid')
            self.git = OwnedFile(git_path, code='source_invalid')
            self.environment = {k: v for k, v in os.environ.items()
                                if not k.upper().startswith(('GIT_', 'PYTHON', 'PONTIUS_'))}
            self.commit = self.command('rev-parse', '--verify', 'HEAD^{commit}').decode().strip()
            require(re.fullmatch('[0-9a-f]{40}', self.commit), 'source_invalid')
            self.tree = self.command('rev-parse', 'HEAD^{tree}').decode().strip()
            self.entries = self.inventory(self.commit)
            baseline = self.inventory(BASE)
            protected = lambda p: p == 'pyproject.toml' or p.startswith(
                ('src/', 'tools/', 'tests/', '.github/'))
            old = {p: oid for p, oid in baseline.items() if protected(p)}
            current = {p: oid for p, oid in self.entries.items() if protected(p)}
            require(set(current) == set(old) | set(ADDITIONS)
                    and all(current[p] == oid for p, oid in old.items() if p not in EXCEPTIONS),
                    'source_invalid')
            expected = self.blobs(self.entries)
            for path, raw in expected.items():
                owned = OwnedFile(root / path, code='source_invalid')
                self.owned[path] = owned
                require(owned.raw == raw, 'source_invalid')
            self.captured = {p: owned.raw for p, owned in self.owned.items()}
            self.manifest = self.raw_manifest(self.captured)
            self.check()
        except BaseException:
            self.close()
            raise

    @staticmethod
    def raw_manifest(files):
        return b''.join(sorted(digest(raw).encode('ascii') + b'  ' + path.encode('utf-8') + b'\n'
                               for path, raw in files.items()))

    def command(self, *args, content=None):
        result = subprocess.run([str(self.git.path), '--no-replace-objects',
            '--no-optional-locks', '-C', str(self.root), *args], env=self.environment,
            input=content, capture_output=True, timeout=60)
        require(result.returncode == 0, 'source_invalid')
        return result.stdout

    def inventory(self, commit):
        entries = {}
        for row in self.command('ls-tree', '-r', '-z', commit).split(b'\0'):
            if row:
                metadata, name = row.split(b'\t', 1)
                mode, kind, oid = metadata.split()
                path = name.decode('utf-8')
                require(mode in (b'100644', b'100755') and kind == b'blob'
                        and path not in entries, 'source_invalid')
                entries[path] = oid.decode('ascii')
        require(entries, 'source_invalid')
        return entries

    def blobs(self, entries):
        output = io.BytesIO(self.command('cat-file', '--batch',
            content=('\n'.join(entries.values()) + '\n').encode('ascii')))
        result = {}
        for path, oid in entries.items():
            header = output.readline().split()
            require(len(header) == 3 and header[:2] == [oid.encode('ascii'), b'blob'],
                    'source_invalid')
            size = int(header[2])
            require(0 <= size <= FILE_LIMIT, 'source_invalid')
            raw = output.read(size)
            require(len(raw) == size and output.read(1) == b'\n', 'source_invalid')
            result[path] = raw
        require(output.read() == b'', 'source_invalid')
        return result

    def check(self):
        self.git.check()
        require(self.command('rev-parse', '--verify', 'HEAD^{commit}').decode().strip()
                == self.commit, 'source_invalid')
        for owned in self.owned.values():
            owned.check()
        actual = set()
        for parent, dirs, files in os.walk(self.root, followlinks=False):
            if Path(parent) == self.root:
                dirs[:] = [name for name in dirs if name != '.git']
            for name in dirs:
                regular(Path(parent) / name, directory=True)
            for name in files:
                path = Path(parent) / name
                if path.name == '.git' and path.parent == self.root:
                    continue
                regular(path)
                if path.suffix == '.py':
                    actual.add(path.relative_to(self.root).as_posix())
        require(actual == {p for p in self.entries if p.endswith('.py')}, 'source_invalid')

    def close(self):
        for owned in self.owned.values():
            owned.close()
        if hasattr(self, 'git'):
            self.git.close()


def admit_authority(source, path, run_root, reader):
    require(path == source.root / AUTHORITY and AUTHORITY in source.captured, 'source_invalid')
    authority = reader.parse_json(source.captured[AUTHORITY])
    reader.shape(authority, 'version source_seal source_manifest_sha256 decision_path '
                 'protocol_sha256 recipe_sha256 run_root runtimes stages')
    require(authority['version'] == VERSION + '-authority-v1'
            and authority['stages'] == ['qualify', 'run']
            and authority['run_root'] == str(run_root)
            and run_root.is_absolute() and run_root.drive.upper() == 'D:', 'source_invalid')
    require(type(authority['source_seal']) is str
            and re.fullmatch('[0-9a-f]{40}', authority['source_seal']), 'source_invalid')
    source.command('merge-base', '--is-ancestor', authority['source_seal'], source.commit)
    sealed = source.inventory(authority['source_seal'])
    require(digest(source.raw_manifest(source.blobs(sealed)))
            == authority['source_manifest_sha256'], 'source_invalid')
    require(all(source.entries.get(p) == oid for p, oid in sealed.items() if p != 'STATUS.md'),
            'source_invalid')
    decision = authority['decision_path']
    require(type(decision) is str and re.fullmatch('docs/decisions/ADR-[0-9]{4}-[^/]+[.]md',
            decision) and decision in source.captured and decision not in sealed, 'source_invalid')
    declaration = (f'Workload invocation authority: `{AUTHORITY}`; '
                   f'SHA-256 `{digest(source.captured[AUTHORITY])}`.')
    require(declaration.encode('ascii') in source.captured[decision].splitlines()
            and source.command('rev-parse', 'refs/remotes/origin/master').decode().strip()
            == source.commit, 'source_invalid')
    require(authority['protocol_sha256'] == digest(source.captured[PROTOCOL])
            and authority['recipe_sha256'] == digest(encode({'version': VERSION + '-recipe-v1'})),
            'source_invalid')
    require(type(authority['runtimes']) is list and len(authority['runtimes']) == 2,
            'source_invalid')
    return authority


def runtime_environment(root, temp):
    required = ('SYSTEMROOT', 'WINDIR', 'COMSPEC', 'SYSTEMDRIVE', 'NUMBER_OF_PROCESSORS',
                'PROCESSOR_ARCHITECTURE', 'PROCESSOR_IDENTIFIER', 'USERPROFILE',
                'LOCALAPPDATA', 'APPDATA', 'PROGRAMDATA')
    environment = {k: v for k, v in os.environ.items() if k.upper() in required}
    environment.update(PYTHONPATH=str(root / 'src'), TEMP=str(temp), TMP=str(temp),
                       PONTIUS_GIT=r'C:\Program Files\Git\cmd\git.exe')
    return environment


def own_runtime(runtime, config, owned):
    require(type(config) is dict and set(config) == {'path', 'sha256'}
            and Path(config['path']) == Path(runtime['executable']).parents[1] / 'pyvenv.cfg',
            'source_invalid')
    for path, sha in ((runtime['executable'], runtime['executable_sha256']),
                      (runtime['resolved_executable'], runtime['resolved_executable_sha256']),
                      (config['path'], config['sha256'])):
        item = OwnedFile(Path(path), code='source_invalid')
        owned.append(item)
        require(digest(item.raw) == sha, 'source_invalid')


def freeze_runtimes(authority, run_root, sources, writer, owned):
    versions = ('3.11.15', '3.14.6')
    executables = ('D:/Pontius-tools/py311/Scripts/python.exe',
                   'D:/Pontius/.venv/Scripts/python.exe')
    runtimes = []
    probe = ('import json,sys,time; print(json.dumps(dict(version=".".join(map(str,'
             'sys.version_info[:3])),resolved=sys._base_executable,'
             'implementation=sys.implementation.name,clocks={name:vars(time.get_clock_info(name)) '
             'for name in ("monotonic","perf_counter")})))')
    for index, entry in enumerate(authority['runtimes']):
        require(type(entry) is dict and set(entry) == {'id', 'version', 'executable', 'source_root'}
                and entry['id'] == versions[index].rsplit('.', 1)[0]
                and entry['version'] == versions[index]
                and Path(entry['executable']) == Path(executables[index]), 'source_invalid')
        root = Path(entry['source_root'])
        source = next((s for s in sources if s.root == root), None)
        if source is None:
            source = FrozenSource(root)
            sources.append(source)
        require(source.commit == sources[0].commit, 'source_invalid')
        environment = runtime_environment(root, run_root / 'temporary' / entry['id'])
        Path(environment['TEMP']).mkdir(parents=True, exist_ok=False)
        observed = subprocess.run([executables[index], '-B', '-P', '-c', probe], cwd=root,
            env=environment, capture_output=True, timeout=30)
        require(observed.returncode == 0 and observed.stderr == b'', 'source_invalid')
        identity = json.loads(observed.stdout)
        require(identity['version'] == versions[index] and identity['implementation'] == 'cpython',
                'source_invalid')
        with OwnedFile(Path(executables[index]), code='source_invalid') as exe, OwnedFile(
                Path(identity['resolved']), code='source_invalid') as resolved:
            runtime = dict(entry, executable=str(exe.path), executable_sha256=digest(exe.raw),
                resolved_executable=str(resolved.path),
                resolved_executable_sha256=digest(resolved.raw),
                run_root=str(run_root), source_sha256=digest(source.manifest),
                protocol_sha256=authority['protocol_sha256'], authorization=str(root / AUTHORITY))
        writer(f'admission/{entry["id"]}-runtime-stdout.bin', observed.stdout)
        writer(f'admission/{entry["id"]}-runtime-stderr.bin', observed.stderr)
        writer(f'admission/{entry["id"]}-source.manifest', source.manifest)
        config_path = Path(runtime['executable']).parents[1] / 'pyvenv.cfg'
        with OwnedFile(config_path, code='source_invalid') as config_file:
            config = dict(path=str(config_path), sha256=digest(config_file.raw))
        own_runtime(runtime, config, owned)
        writer(f'admission/{entry["id"]}-venv.json', encode(config))
        runtimes.append(runtime)
    return runtimes


def stage_sample(stage):
    os.write(1, encode({'stage': stage, 'pid': os.getpid()}))
    require(os.read(0, 1) == b'G', 'worker_failed')


def diagnostic(root, argv, output):
    """Observe the unchanged entry point before Admission imports any poker module."""
    require(not any(n == 'pontius' or n.startswith('pontius.') for n in sys.modules),
            'source_invalid')
    observer, previous = Observer(root), sys.argv
    sys.argv = [str(root / TOOLS['session'][0]), *argv]
    try:
        sys.setprofile(observer)
        session = load_tool('session', root)
        code = session.main(argv)
    finally:
        sys.setprofile(None)
        sys.argv = previous
        with output.open('xb') as stream:
            stream.write(encode(observer.events))
    return code


class CapturedWire:
    """Feed retained bytes through the existing host validator, outside measured intervals."""
    def __init__(self, raw):
        self.rows = iter(raw.splitlines(keepends=True))
        self.received = []
        self.startup_deadline = time.monotonic() + 60

    def deadline(self):
        return time.monotonic() + 60

    def send(self, raw, deadline):
        require(type(raw) is bytes and raw.endswith(b'\n'), 'parity_failed')

    def receive(self, deadline):
        try:
            raw = next(self.rows)
        except StopIteration:
            return None
        self.received.append(raw)
        return raw


def session_observations(raw, cell, reference, root, reader, raw_events, validator):
    # Replay validates the original wire schema and full actions using the accepted host.
    report = reader.parse_json(raw)
    require(report['status'] == 'completed' and report['completed_hands'] == 1
            and report['failure_reason'] is None and report['secondary_failures'] == [],
            'worker_failed')
    params = cell['parameters']
    host, source, modules = validator
    config_raw = Path(params['session_path']).read_bytes()
    config = json.loads(config_raw)
    blueprint_raw = Path(params['blueprint_path']).read_bytes()
    blueprint = modules.codec.decode_blueprint(blueprint_raw)
    hand = report['hands'][0]['result']
    require(hand['status'] == 'completed' and hand['child_exit_code'] == 0
            and hand['capture_truncated'] is False and not hand['secondary_failures'],
            'worker_failed')
    child_raw = base64.b64decode(hand['child_stdout_base64'], validate=True)
    frames = [reader.parse_json(line) for line in child_raw.splitlines()]
    require(frames and frames[0]['type'] == 'ready', 'parity_failed')
    child_id = frames[0]['session_id']
    table_config = host.TableInput.decode(encode(dict(
        {k: v for k, v in config.items() if k != 'hands'}, **config['hands'][0],
        version=host.INPUT_VERSION)), modules)
    table, wire = host.Table(table_config, modules, child_id), CapturedWire(child_raw)
    baseline = params['strategy'] == 'baseline-rules-v1'
    identity = (modules.providers.make_provider(params['strategy'], blueprint).identity
                if baseline else None)
    consumer = host.WireConsumer(wire, source, table, digest(blueprint_raw), blueprint.digest,
                                identity, blueprint if baseline else None)
    consumer.ready()
    event, decisions = table.start_event(), []
    while event is not None:
        pending = None
        if table.expects_action():
            selection = blueprint.action_for(cards=table.views[table.config.controlled_seat],
                betting=table.state, decision=table.state.legal_decision())
            pending = (len(table.state.history), selection.table_hit)
        before = len(wire.received)
        consumer.exchange(event)
        if pending is not None:
            received = [reader.parse_json(line) for line in wire.received[before:]]
            values = [r['decision'] for r in received if r['type'] == 'event_result'
                      and r['decision'] is not None]
            require(len(values) == 1, 'parity_failed')
            value, timing = values[0], values[0]['timing']
            origin = value.get('selection_origin', 'blueprint')
            decisions.append(dict(id=f'{cell["id"]}-a{value["action_index"]}',
                hand_id=value['hand_id'], event_index=value['event_index'],
                action_index=value['action_index'], street=value['street'],
                history_atoms=pending[0], hit=pending[1], first=value['action_index'] == 1,
                elapsed_ns=timing['elapsed_ns'],
                compute_ns=round(timing['response_compute_seconds'] * 1e9),
                uninstrumented_ns=round(timing['response_uninstrumented_seconds'] * 1e9),
                work_cutoff=timing['work_cutoff_crossed'], deadline=timing['deadline_crossed'],
                fallback_used=origin == 'fallback' if baseline else True,
                selection_origin=origin))
        event = table.next_event()
    settlement = consumer.complete()
    require(next(wire.rows, None) is None, 'parity_failed')
    require(settlement == hand['settlement'], 'parity_failed')
    actions = [{k: row[k] for k in ('seat', 'street', 'action')} for row in hand['applied_actions']]
    require(actions == reference['actions'] and all(settlement[k] == reference['settlement'][k]
            for k in ('payouts', 'final_stacks', 'pots')), 'parity_failed')
    totals = [r for r in frames if r['type'] == 'hand_result']
    require(len(totals) == 1, 'parity_failed')
    preparation = [dict(hand_id=child_id, **{key: totals[0][key] for key in (
        'preparation_compute_seconds', 'post_terminal_compute_seconds',
        'accounting_complete', 'interrupted_response_count')})]
    return dict(raw_events=raw_events, actions=decisions, preparation=preparation,
                session_status=report['status'], settlement=settlement,
                reference_id=reference['id'])


def file_manifest(root, writer, name):
    rows = []
    for path in sorted(root.rglob('*')):
        if path.is_file() and path != root / name:
            with OwnedFile(path) as owned:
                rows.append(dict(path=path.relative_to(root).as_posix(),
                                 sha256=digest(owned.raw), bytes=len(owned.raw)))
    return writer(name, encode(dict(version=VERSION + '-manifest-v1', files=rows)))


def claim_stage(root, writer, stage, source, authority_raw):
    nonce = os.urandom(32)
    writer(stage + '-claim.json', encode(dict(version=VERSION + '-claim-v1', stage=stage,
        nonce_sha256=digest(nonce), controller_pid=os.getpid(), source_commit=source.commit,
        authority_sha256=digest(authority_raw), source_manifest_sha256=digest(source.manifest))))
    return nonce


def verify_gate(stream, claim):
    require(type(claim) is dict and set(claim) == {'version', 'stage', 'nonce_sha256',
            'controller_pid', 'source_commit', 'authority_sha256', 'source_manifest_sha256'}
            and claim['version'] == VERSION + '-claim-v1'
            and claim['stage'] in ('qualify', 'run'), 'source_invalid')
    raw = stream.read(32)
    require(type(raw) is bytes and len(raw) == 32 and digest(raw) == claim['nonce_sha256']
            and type(claim['controller_pid']) is int and claim['controller_pid'] > 0
            and process_alive(claim['controller_pid']), 'source_invalid')


def worker_entry(args):
    # This capability travels only through the controller-owned stdin pipe. The controller
    # keeps whole-tree and input handles and validates them before and after every worker.
    stage = 'qualify' if args.cell == 'qualification' else 'run'
    with OwnedFile(args.run_root / (stage + '-claim.json')) as marker:
        claim = json.loads(marker.raw)
        verify_gate(sys.stdin.buffer, claim)
        with OwnedFile(args.authorization, code='source_invalid') as authority:
            require(args.authorization == args.source_root / AUTHORITY
                    and digest(authority.raw) == claim['authority_sha256'], 'source_invalid')
            parsed = json.loads(authority.raw)
            require(parsed['run_root'] == str(args.run_root), 'source_invalid')
        git = Path(os.environ.get('PONTIUS_GIT', ''))
        require(git == Path(r'C:\Program Files\Git\cmd\git.exe'), 'source_invalid')
        regular(git)
        checked = subprocess.run([str(git), '--no-replace-objects', '--no-optional-locks',
            '-C', str(args.source_root), 'rev-parse', 'HEAD'], capture_output=True, timeout=30)
        require(checked.returncode == 0
                and checked.stdout.decode().strip() == claim['source_commit'],
                'source_invalid')
        runtimes = json.loads((args.run_root / 'runtimes.json').read_bytes())
        runtime = next((r for r in runtimes if Path(r['source_root']) == args.source_root
                        and r['version'] == '.'.join(map(str, sys.version_info[:3]))), None)
        require(runtime is not None and Path(runtime['executable']) == Path(sys.executable)
                and Path(runtime['resolved_executable']) == Path(sys._base_executable),
                'source_invalid')
        manifest_path = args.run_root / f'admission/{runtime["id"]}-source.manifest'
        source_manifest = manifest_path.read_bytes()
        require(digest(source_manifest) == runtime['source_sha256']
                == claim['source_manifest_sha256'], 'source_invalid')
        expected = {}
        for row in source_manifest.splitlines():
            sha, path = row.split(b'  ', 1)
            expected[path.decode('utf-8')] = sha.decode('ascii')
        captured = {}
        for relative in (ADDITIONS[:4] + (TOOLS['host'][0], TOOLS['session'][0])):
            with OwnedFile(args.source_root / relative, code='source_invalid') as owned:
                require(digest(owned.raw) == expected[relative], 'source_invalid')
                captured[relative] = owned.raw
        reader = load_tool('report', args.source_root, captured)
        writer = Writer(args.run_root)
        if stage == 'qualify':
            stage_sample('ready')
            population = load_tool('population', args.source_root, captured)
            manifest = population.build_population({'version': VERSION + '-recipe-v1'}, writer)
            writer('population.json', encode(manifest))
            writer('plan.json', encode(population.freeze_plan(manifest, runtimes)))
            stage_sample('final')
            return 0
        plan = reader.parse_json((args.run_root / 'plan.json').read_bytes())
        cells = [c for c in plan['cells'] if c['id'] == args.cell]
        require(len(cells) == 1 and cells[0]['runtime'] == runtime['id'], 'input_invalid')
        cell = cells[0]
        intent = reader.parse_json((args.run_root / f'cells/{args.cell}/intent.json').read_bytes())
        require(intent['cell'] == cell, 'input_invalid')
        if cell['kind'] == 'session':
            require(cell['parameters']['diagnostic'] is True, 'input_invalid')
            params = cell['parameters']
            return diagnostic(args.source_root, ['--session', params['session_path'],
                '--blueprint', params['blueprint_path'], '--session-id', params['session_id'],
                '--strategy', params['strategy'], '--auto', '--format', 'json'],
                args.run_root / f'cells/{args.cell}/profile.json')
        stage_sample('ready')
        population = load_tool('population', args.source_root, captured)
        measure = load_tool('measure', args.source_root, captured)
        manifest = reader.parse_json((args.run_root / 'population.json').read_bytes())
        metadata = next(a for a in manifest['artifacts'] if a['size'] == cell['size'])
        selections = reader.parse_json(
            (args.run_root / manifest['selections']['path']).read_bytes())
        observation = measure.measure_cell(cell, dict(
            artifact_path=args.run_root / metadata['file']['path'], artifact_metadata=metadata,
            selections=selections, population=population, clock=time.perf_counter_ns,
            stage=stage_sample))
        writer(f'cells/{args.cell}/observations.json', encode(observation))
        if cell['kind'] not in ('memory_traced', 'memory_untraced'):
            stage_sample('final')
        return 0


def qualify(args, source, reader, sources, authority):
    regular(args.run_root.parent, directory=True)
    args.run_root.mkdir(exist_ok=False)
    writer, owned = Writer(args.run_root), []
    started = time.perf_counter_ns()
    try:
        nonce = claim_stage(args.run_root, writer, 'qualify', source, source.captured[AUTHORITY])
        runtimes = freeze_runtimes(authority, args.run_root, sources, writer, owned)
        writer('runtimes.json', encode(runtimes))
        runtime = runtimes[0]
        argv = [runtime['executable'], '-B', '-P', str(source.root / ADDITIONS[0]),
                'worker', '--source-root', str(source.root), '--run-root', str(args.run_root),
                '--authorization', str(args.authorization), '--cell', 'qualification']
        environment = runtime_environment(source.root, args.run_root / 'temporary' / runtime['id'])
        writer('qualification-intent.json', encode(dict(
            argv=argv, recipe_sha256=authority['recipe_sha256'])))
        writer('qualification-environment.json', encode(environment))
        owned.extend(OwnedFile(args.run_root / ref['path']) for ref in writer.references)
        for item in (*sources, *owned):
            item.check()
        remaining = 1_800_000_000_000 - (time.perf_counter_ns() - started)
        require(remaining > 0, 'budget_exhausted')
        result = supervise(argv, source.root, environment, timeout_ns=remaining,
                           worker=True, gate=nonce)
        for name in ('stdout', 'stderr'):
            writer(f'qualification-{name}.bin', result.pop(name))
        try:
            for item in (*sources, *owned):
                item.check()
        except (OSError, ValueError) as error:
            result['secondary'].append(getattr(error, 'code', 'input_invalid'))
        result['stage_ns'] = time.perf_counter_ns() - started
        writer('qualification-result.json', encode(result))
        require(result['cause'] is None and not result['secondary']
                and result['cleanup']['verified'], result['cause'] or
                (result['secondary'][0] if result['secondary'] else 'cleanup_failed'))
        plan = reader.parse_json((args.run_root / 'plan.json').read_bytes())
        reader.validate_plan(plan)
        require(plan['runtimes'] == runtimes, 'parity_failed')
        manifest = file_manifest(args.run_root, writer, 'qualification-manifest.json')
        writer('qualified.json', encode(dict(version=VERSION + '-qualified-v1',
            source_commit=source.commit,
            plan_sha256=digest((args.run_root / 'plan.json').read_bytes()), manifest=manifest)))
        return 0
    except (Exception, KeyboardInterrupt) as error:
        stage_refusal(writer, reader, 'qualification-refusal.json', error)
        file_manifest(args.run_root, writer, 'manifest.json')
        return 1
    finally:
        for item in owned:
            item.close()


def stage_refusal(writer, reader, name, error):
    code = getattr(error, 'code', 'worker_failed')
    writer(name, encode(dict(cause=code if code in reader.CAUSES else 'worker_failed',
        interrupted=isinstance(error, KeyboardInterrupt) or code == 'interrupted',
        original_code=str(code), exception_type=type(error).__name__, detail=str(error))))


def run(args, source, reader, sources, authority):
    writer, owned = Writer(args.run_root), []
    nonce = claim_stage(args.run_root, writer, 'run', source, source.captured[AUTHORITY])
    try:
        qualified_file = OwnedFile(args.run_root / 'qualified.json')
        owned.append(qualified_file)
        qualified = reader.parse_json(qualified_file.raw)
        require(qualified['source_commit'] == source.commit, 'source_invalid')
        reader.file_ref(qualified['manifest'])
        qualification_file = OwnedFile(args.run_root / qualified['manifest']['path'])
        owned.append(qualification_file)
        raw = qualification_file.raw
        require(digest(raw) == qualified['manifest']['sha256'], 'input_invalid')
        for reference in reader.parse_json(raw)['files']:
            reader.file_ref(reference)
            item = OwnedFile(args.run_root / reference['path'])
            owned.append(item)
            require(digest(item.raw) == reference['sha256'] and len(item.raw) == reference['bytes'])
        plan_raw = (args.run_root / 'plan.json').read_bytes()
        require(digest(plan_raw) == qualified['plan_sha256'], 'input_invalid')
        plan = reader.parse_json(plan_raw)
        reader.validate_plan(plan)
        population = reader.parse_json((args.run_root / 'population.json').read_bytes())
        require(digest(encode(population)) == plan['population_sha256'], 'input_invalid')
        host = load_tool('host', source.root, source.captured)
        validation_source = host.Source(source.root)
        validator = (host, validation_source, validation_source.load())
        population_tool = load_tool('population', source.root, source.captured)
        require(encode(plan) == encode(population_tool.freeze_plan(population, plan['runtimes'])),
                'input_invalid')
        environments = {}
        for cell in plan['cells']:
            runtime = next(r for r in plan['runtimes'] if r['id'] == cell['runtime'])
            writer(f'cells/{cell["id"]}/intent.json', encode(dict(version=VERSION + '-intent-v1',
                cell_id=cell['id'], cell=cell, source_sha256=runtime['source_sha256'],
                protocol_sha256=runtime['protocol_sha256'],
                population_sha256=plan['population_sha256'])))
            environments[cell['id']] = runtime_environment(
                Path(runtime['source_root']), args.run_root / 'temporary' / runtime['id'])
            writer(f'cells/{cell["id"]}/environment.json', encode(environments[cell['id']]))
        owned.extend(OwnedFile(args.run_root / ref['path']) for ref in writer.references)
        admission_error = None
        try:
            admit_run_runtimes(plan, args.run_root, source, sources, reader, owned)
        except (Exception, KeyboardInterrupt) as error:
            admission_error = error
        stop, started, finished, terminals = None, None, None, []
        for cell in plan['cells']:
            runtime = next(r for r in plan['runtimes'] if r['id'] == cell['runtime'])
            result = dict(version=VERSION + '-result-v1', cell_id=cell['id'], status='unattempted',
                cause=stop, secondary=[], observations={}, files=[], outer_ns=None, exit_code=None,
                cleanup=dict(verified=False, active=None),
                captures=dict(stdout=None, stderr=None, truncated=False))
            if stop is None:
                native = None
                try:
                    if admission_error is not None:
                        raise admission_error
                    for item in (*sources, *owned):
                        item.check()
                    now = time.perf_counter_ns()
                    remaining = 3_600_000_000_000 - (0 if started is None else now - started)
                    require(remaining > 0, 'budget_exhausted')
                    direct = cell['kind'] != 'session'
                    native = supervise(cell['argv'], Path(runtime['source_root']),
                        environments[cell['id']], timeout_ns=remaining, worker=direct,
                        gate=nonce if direct or cell['parameters'].get('diagnostic') else b'')
                    if started is None:
                        started = native['launch_ns']
                    finished = native['launch_ns'] + native['outer_ns']
                    writer(f'cells/{cell["id"]}/supervision.json', encode(
                        {k: v for k, v in native.items() if k not in ('stdout', 'stderr')}))
                    for name in ('stdout', 'stderr'):
                        result['captures'][name] = writer(
                            f'cells/{cell["id"]}/{name}.bin', native[name])
                    result.update(outer_ns=native['outer_ns'], exit_code=native['exit_code'],
                                  cleanup=native['cleanup'], secondary=native['secondary'])
                    result['captures']['truncated'] = native['truncated']
                    try:
                        for item in (*sources, *owned):
                            item.check()
                    except (OSError, ValueError) as error:
                        code = getattr(error, 'code', 'input_invalid')
                        if native['cause'] is None:
                            native['cause'] = code
                        else:
                            result['secondary'].append(code)
                    require(native['cause'] is None, native['cause'] or 'worker_failed')
                    require(native['cleanup']['verified'] and not native['secondary'],
                            'cleanup_failed')
                    if direct:
                        observations = reader.parse_json((args.run_root /
                            f'cells/{cell["id"]}/observations.json').read_bytes())
                        observations['memory_samples'] = native['samples']
                    else:
                        params = cell['parameters']
                        ordinal = params['deal'] * 72 + params['seat'] * 12 + params['lineup'] * 2
                        ordinal += int(params['strategy'] == 'baseline-rules-v1')
                        chunk = args.run_root / f'population/query-{ordinal // 128:03d}.jsonl'
                        reference = reader.parse_json(
                            chunk.read_bytes().splitlines()[ordinal % 128])
                        events = []
                        if params['diagnostic']:
                            profile = args.run_root / f'cells/{cell["id"]}/profile.json'
                            events = reader.parse_json(profile.read_bytes())
                            events = [dict(e, ns=e['ns'] - native['launch_ns']) for e in events]
                            reader.reduce_spans(events, native['outer_ns'])
                        observations = session_observations(native['stdout'], cell, reference,
                            source.root, reader, events, validator)
                    reader.validate_observations(observations, cell)
                    result.update(status='completed', observations=observations)
                except (Exception, KeyboardInterrupt) as error:
                    code = getattr(error, 'code', 'worker_failed')
                    interrupted = isinstance(error, KeyboardInterrupt) or code == 'interrupted'
                    if code not in reader.CAUSES:
                        writer(f'cells/{cell["id"]}/failure.json', encode(dict(
                            code=str(code), exception_type=type(error).__name__,
                            detail=str(error))))
                        code = 'worker_failed'
                    result.update(status='interrupted' if interrupted else 'failed',
                                  cause=code)
                    stop = code
            for path in sorted((args.run_root / f'cells/{cell["id"]}').iterdir()):
                if path.is_file():
                    with OwnedFile(path) as artifact:
                        result['files'].append(dict(path=path.relative_to(args.run_root).as_posix(),
                            sha256=digest(artifact.raw), bytes=len(artifact.raw)))
            result['secondary'] = list(dict.fromkeys(result['secondary']))
            reader.validate_result(result)
            writer(f'cells/{cell["id"]}/result.json', encode(result))
            terminals.append(dict(cell_id=cell['id'], status=result['status']))
        writer('terminal.json', encode(dict(version=VERSION + '-terminal-v1', cells=terminals)))
        writer('run-envelope.json', encode(dict(started_ns=started, finished_ns=finished,
                                               stop=stop)))
        file_manifest(args.run_root, writer, 'manifest.json')
        return 0 if stop is None else 1
    except (Exception, KeyboardInterrupt) as error:
        stage_refusal(writer, reader, 'run-refusal.json', error)
        if not (args.run_root / 'manifest.json').exists():
            file_manifest(args.run_root, writer, 'manifest.json')
        return 1
    finally:
        for item in owned:
            item.close()


def admit_run_runtimes(plan, root, source, sources, reader, owned):
    for runtime in plan['runtimes']:
        if not any(s.root == Path(runtime['source_root']) for s in sources):
            sources.append(FrozenSource(Path(runtime['source_root'])))
        matched = next(s for s in sources if s.root == Path(runtime['source_root']))
        require(matched.commit == source.commit and digest(matched.manifest)
                == runtime['source_sha256'], 'source_invalid')
        config = reader.parse_json((root / f'admission/{runtime["id"]}-venv.json').read_bytes())
        own_runtime(runtime, config, owned)


class Observer:
    def __init__(self, root, clock=time.perf_counter_ns):
        self.clock, self.events = clock, []
        self.points = {(os.path.normcase(str(root / TOOLS[kind][0])), name): kind + ':' + name
                       for kind, names in POINTS.items() for name in names}

    def __call__(self, frame, event, arg):
        if event in ('call', 'return'):
            code = frame.f_code
            point = self.points.get((os.path.normcase(code.co_filename), code.co_qualname))
            if point is not None:
                require(len(self.events) < 1_000_000, 'capture_limit')
                self.events.append({'event': event, 'point': point, 'ns': self.clock()})


def process_api():
    api = ctypes.WinDLL('kernel32', use_last_error=True)
    for name, args, result in (
        ('OpenProcess', [ctypes.c_ulong, ctypes.c_int, ctypes.c_ulong], ctypes.c_void_p),
        ('CloseHandle', [ctypes.c_void_p], ctypes.c_int),
        ('WaitForSingleObject', [ctypes.c_void_p, ctypes.c_ulong], ctypes.c_ulong),
        ('IsProcessInJob', [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p], ctypes.c_int),
        ('K32GetProcessMemoryInfo', [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_ulong],
         ctypes.c_int),
    ):
        function = getattr(api, name)
        function.argtypes, function.restype = args, result
    return api


def process_alive(pid):
    api = process_api()
    handle = api.OpenProcess(0x100000, False, pid)
    if not handle:
        require(ctypes.get_last_error() == 87, 'cleanup_failed')
        return False
    try:
        value = api.WaitForSingleObject(handle, 0)
        require(value in (0, 258), 'cleanup_failed')
        return value == 258
    finally:
        require(api.CloseHandle(handle), 'cleanup_failed')


class MemorySampler:
    def __init__(self, pid, job):
        require(type(pid) is int and pid > 0, 'worker_failed')
        self.api, self.pid = process_api(), pid
        self.handle = self.api.OpenProcess(0x101010, False, pid)
        require(self.handle, 'worker_failed')
        belongs = ctypes.c_int()
        try:
            require(self.api.IsProcessInJob(self.handle, job.handle, ctypes.byref(belongs))
                    and belongs.value == 1, 'worker_failed')
        except BaseException:
            self.close()
            raise

    def sample(self):
        class Counters(ctypes.Structure):
            _fields_ = [('cb', ctypes.c_ulong), ('faults', ctypes.c_ulong)] + [
                (name, ctypes.c_size_t) for name in ('peak_working_set', 'working_set',
                 'peak_paged', 'paged', 'peak_nonpaged', 'nonpaged', 'pagefile',
                 'peak_private_commit', 'private_commit')]
        value = Counters()
        value.cb = ctypes.sizeof(value)
        require(self.api.K32GetProcessMemoryInfo(self.handle, ctypes.byref(value), value.cb),
                'worker_failed')
        return {name: getattr(value, name) for name in (
            'private_commit', 'working_set', 'peak_private_commit', 'peak_working_set')}

    def close(self):
        if self.handle:
            handle, self.handle = self.handle, None
            require(self.api.CloseHandle(handle), 'cleanup_failed')


def supervise(argv, root, environment, *, timeout_ns, stdout_limit=64 * 1024 * 1024,
              stderr_limit=256 * 1024, stop=None, worker=False, gate=b''):
    """Own a suspended worker before it executes; fault seams only request real cleanup."""
    host = load_tool('host', root)
    job, process, sampler, cause = host.Job(), None, None, None
    secondary, samples, threads, streams = [], [], [], [bytearray(), bytearray()]
    overflow, messages = threading.Event(), queue.Queue()
    truncated, exit_code, active = False, None, None
    launched = time.perf_counter_ns()

    def capture(pipe, index, limit):
        pending = bytearray()
        try:
            while True:
                chunk = os.read(pipe.fileno(), 16384)
                if not chunk:
                    return
                available = max(0, limit - len(streams[index]))
                streams[index].extend(chunk[:available])
                if len(chunk) > available:
                    overflow.set()
                if worker and index == 0:
                    pending.extend(chunk)
                    while b'\n' in pending:
                        line, _, tail = pending.partition(b'\n')
                        pending = bytearray(tail)
                        messages.put(bytes(line))
                    if len(pending) > 8192:
                        overflow.set()
        except OSError:
            messages.put(None)

    try:
        process = subprocess.Popen(argv, cwd=root, env=environment, stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=0x08000004)
        job.assign(process)
        for index, (pipe, limit) in enumerate(((process.stdout, stdout_limit),
                                               (process.stderr, stderr_limit))):
            thread = threading.Thread(target=capture, args=(pipe, index, limit), daemon=True)
            thread.start()
            threads.append(thread)
        job.resume(process)
        if gate:
            process.stdin.write(gate)
            process.stdin.flush()
        while True:
            elapsed = time.perf_counter_ns() - launched
            if overflow.is_set():
                truncated, cause = True, 'capture_limit'
                break
            if elapsed >= timeout_ns:
                cause = 'budget_exhausted'
                break
            if stop is not None:
                cause = stop(elapsed, tuple(samples))
                if cause is not None:
                    break
            while not messages.empty():
                raw = messages.get_nowait()
                require(raw is not None, 'worker_failed')
                message = json.loads(raw)
                require(type(message) is dict and set(message) == {'stage', 'pid'}
                        and message['stage'] in ('idle', 'read', 'decode', 'prepare', 'first',
                                                'ready', 'final'), 'worker_failed')
                if sampler is None:
                    sampler = MemorySampler(message['pid'], job)
                require(message['pid'] == sampler.pid, 'worker_failed')
                value = dict(sampler.sample(), ns=time.perf_counter_ns() - launched,
                             stage=message['stage'], pid=sampler.pid)
                samples.append(value)
                if value['private_commit'] > 3 * 1024 ** 3:
                    cause = 'resource_limit'
                elif stop is not None:
                    cause = stop(value['ns'], tuple(samples))
                if cause is not None:
                    break
                process.stdin.write(b'G')
                process.stdin.flush()
            if cause is not None:
                break
            if sampler is not None:
                if sampler.api.WaitForSingleObject(sampler.handle, 0) == 258:
                    value = dict(sampler.sample(), ns=time.perf_counter_ns() - launched,
                                 stage='periodic', pid=sampler.pid)
                    samples.append(value)
                    if value['private_commit'] > 3 * 1024 ** 3:
                        cause = 'resource_limit'
                        break
            if process.poll() is not None:
                exit_code = process.returncode
                cause = None if exit_code == 0 else 'worker_failed'
                break
            time.sleep(0.05)
        if worker and sampler is None and cause is None:
            cause = 'worker_failed'
    except KeyboardInterrupt:
        cause = 'interrupted'
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        cause = getattr(error, 'code', 'worker_failed')
    finally:
        cleanup_start = time.perf_counter_ns()
        try:
            if cause is None:
                # A signalled redirector and the job's active census need not settle
                # in the same instant. Observe descendants before judging completion.
                verification_end = min(launched + timeout_ns, cleanup_start + 10_000_000_000)
                while job.active() and time.perf_counter_ns() < verification_end:
                    time.sleep(0.01)
                if job.active():
                    cause = 'worker_failed'
            if job.active():
                job.terminate()
            if process is not None:
                exit_code = process.wait(timeout=10)
            deadline = time.monotonic() + 10
            while job.active() and time.monotonic() < deadline:
                time.sleep(0.01)
            active = job.active()
            require(active == 0, 'cleanup_failed')
        except (OSError, ValueError, subprocess.SubprocessError):
            secondary.append('cleanup_failed')
        outer_ns = time.perf_counter_ns() - launched
        for thread in threads:
            thread.join(timeout=5)
            if thread.is_alive():
                secondary.append('cleanup_failed')
        if overflow.is_set():
            truncated = True
            if cause is None:
                cause = 'capture_limit'
            elif cause != 'capture_limit':
                secondary.append('capture_limit')
        for item in (sampler, job):
            if item is not None:
                try:
                    item.close()
                except (OSError, ValueError):
                    secondary.append('cleanup_failed')
        if process is not None:
            for stream in (process.stdin, process.stdout, process.stderr):
                if stream is not None:
                    try:
                        stream.close()
                    except OSError:
                        secondary.append('cleanup_failed')
    return {'cause': cause, 'secondary': list(dict.fromkeys(secondary)),
            'exit_code': exit_code, 'stdout': bytes(streams[0]), 'stderr': bytes(streams[1]),
            'truncated': truncated or overflow.is_set(), 'samples': samples,
            'redirector_pid': process.pid if process is not None else None,
            'launch_ns': launched, 'outer_ns': outer_ns,
            'cleanup_ns': time.perf_counter_ns() - cleanup_start,
            'cleanup': {'verified': not secondary and active == 0, 'active': active}}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('qualify', 'run', 'read', 'worker'))
    for name in ('source-root', 'run-root', 'authorization'):
        parser.add_argument('--' + name, required=name != 'authorization', type=Path)
    parser.add_argument('--cell')
    sources = []
    try:
        args = parser.parse_args(argv)
        require(os.name == 'nt' and sys.implementation.name == 'cpython'
                and sys.dont_write_bytecode and sys.flags.safe_path, 'source_invalid')
        require(args.source_root.is_absolute() and args.run_root.is_absolute()
                and args.source_root == Path(__file__).absolute().parents[1])
        require((args.cell is not None) == (args.mode == 'worker'))
        if args.mode == 'worker':
            require(args.authorization is not None and args.authorization.is_absolute(),
                    'source_invalid')
            return worker_entry(args)
        source = FrozenSource(args.source_root)
        sources.append(source)
        reader = load_tool('report', source.root, source.captured)
        if args.mode == 'read':
            require(args.authorization is None and args.cell is None)
            report = reader.read_run(args.run_root)
            sys.stdout.buffer.write(encode(report))
            return 0
        require(args.authorization is not None and args.authorization.is_absolute(),
                'source_invalid')
        require(sys.version_info[:3] == (3, 11, 15)
                and Path(sys.executable) == Path('D:/Pontius-tools/py311/Scripts/python.exe'),
                'source_invalid')
        authority = admit_authority(source, args.authorization, args.run_root, reader)
        action = qualify if args.mode == 'qualify' else run
        return action(args, source, reader, sources, authority)
    except SystemExit as error:
        return int(error.code)
    except (OSError, ValueError, KeyError, StopIteration) as error:
        sys.stderr.write(getattr(error, 'code', 'input_invalid') + '\n')
        return 1
    finally:
        for source in sources:
            source.close()


if __name__ == '__main__':
    raise SystemExit(main())
