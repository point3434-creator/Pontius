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
CONTROL_PREFIX = b'PONTIUS_WORKLOAD_CONTROL '
GRANT_PREFIX = b'PONTIUS_WORKLOAD_GRANT '
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
    """Publish complete bytes once; interrupted staging remains raw evidence."""
    def __init__(self, root, limit=FILE_LIMIT):
        regular(root, directory=True)
        self.root, self.limit, self.references = root, limit, []

    def __call__(self, relative, raw):
        require(type(relative) is str and type(raw) is bytes
                and relative and '\\' not in relative and ':' not in relative
                and all(p not in ('', '.', '..') for p in relative.split('/')))
        require(len(raw) <= self.limit, 'capture_limit')
        target = self.root / relative
        require(target.is_relative_to(self.root))
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            regular(target.parent, directory=True)
            staging = self.root / 'retention-staging'
            staging.mkdir(exist_ok=True)
            regular(staging, directory=True)
            temporary = staging / (os.urandom(24).hex() + '.bin')
            with temporary.open('xb') as output:
                output.write(raw)
                output.flush()
                os.fsync(output.fileno())
            # On Windows rename fails when the destination already exists. Both
            # objects are on the claimed run volume; replacement is never used.
            os.rename(temporary, target)
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
    def __init__(self, root, *, delegated=False):
        self.root, self.owned, self.delegated = root, {}, delegated
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
                if delegated and path not in (*ADDITIONS[:4], AUTHORITY, PROTOCOL,
                                             *(value[0] for value in TOOLS.values())):
                    continue
                owned = OwnedFile(root / path, code='source_invalid')
                self.owned[path] = owned
                require(owned.raw == raw, 'source_invalid')
            self.captured = expected
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
        if self.delegated:
            # The worker admits exact Git/authority and its execution bytes here.
            # Whole working-tree ownership is accepted only through the native
            # controller's one-use grant, before any workload dispatch.
            return
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
                fallback_used=origin == 'blueprint_fallback' if baseline else True,
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


def file_manifest(root, writer, name, *, check=None):
    rows = []
    for path in root.rglob('*'):
        if check is not None:
            check()
        if path.is_file() and path != root / name:
            with OwnedFile(path) as item:
                rows.append(dict(path=path.relative_to(root).as_posix(),
                                 sha256=digest(item.raw), bytes=len(item.raw)))
    if check is not None:
        check()
    rows.sort(key=lambda item: item['path'])
    return writer(name, encode(dict(version=VERSION + '-manifest-v1', files=rows)))


def claim_stage(root, writer, stage, source, authority_raw):
    require(stage in ('qualify', 'run'), 'source_invalid')
    controller = ProcessIdentity(os.getpid())
    try:
        claim = dict(version=VERSION + '-claim-v2', stage=stage, controller_pid=controller.pid,
            controller_created_100ns=controller.created, source_commit=source.commit,
            source_tree=source.tree, authority_sha256=digest(authority_raw),
            source_manifest_sha256=digest(source.manifest), run_root=str(root))
        writer(stage + '-claim.json', encode(claim))
        return claim
    finally:
        controller.close()


def grant_paths(stage, cell_id):
    require(stage in ('qualify', 'run') and type(cell_id) is str
            and re.fullmatch('[A-Za-z0-9_.-]{1,128}', cell_id)
            and (stage == 'qualify') == (cell_id == 'qualification'), 'source_invalid')
    prefix = 'qualification-' if stage == 'qualify' else f'cells/{cell_id}/'
    return prefix + 'worker-grant-intent.json', prefix + 'worker-grant.json'


def grant_intent(claim, source, runtime, cell, root, plan_raw, nonce_sha256):
    require(type(claim) is dict and set(claim) == set(('version stage controller_pid '
        'controller_created_100ns source_commit source_tree source_manifest_sha256 '
        'authority_sha256 run_root').split()) and claim['version'] == VERSION + '-claim-v2',
        'source_invalid')
    require(claim['source_commit'] == source.commit and claim['source_tree'] == source.tree
            and claim['source_manifest_sha256'] == digest(source.manifest)
            and claim['authority_sha256'] == digest(source.captured[AUTHORITY])
            and claim['run_root'] == str(root) and Path(runtime['source_root']) == source.root
            and runtime['source_sha256'] == digest(source.manifest), 'source_invalid')
    require(type(nonce_sha256) is str and re.fullmatch('[0-9a-f]{64}', nonce_sha256),
            'source_invalid')
    grant_paths(claim['stage'], cell['id'])
    require((plan_raw is None) == (claim['stage'] == 'qualify'), 'source_invalid')
    return dict(version=VERSION + '-worker-grant-intent-v1', stage=claim['stage'],
        cell_id=cell['id'], runtime_id=runtime['id'], source_commit=source.commit,
        source_tree=source.tree, source_manifest_sha256=digest(source.manifest),
        authority_sha256=claim['authority_sha256'], stage_claim_sha256=digest(encode(claim)),
        runtime_sha256=digest(encode(runtime)), plan_sha256=(None if plan_raw is None
        else digest(plan_raw)), cell_sha256=digest(encode(cell)),
        controller_pid=claim['controller_pid'],
        controller_created_100ns=claim['controller_created_100ns'], source_root=str(source.root),
        run_root=str(root), nonce_sha256=nonce_sha256)


def prepare_worker_grant(claim, source, runtime, cell, writer, *, plan_raw=None, checks=()):
    """Reserve this stage/cell once before launch; secret bytes stay off retained files."""
    require(claim['controller_pid'] == os.getpid() and checks, 'source_invalid')
    controller = ProcessIdentity(os.getpid(), created=claim['controller_created_100ns'])
    owned = []
    try:
        nonce = os.urandom(32)
        intent = grant_intent(claim, source, runtime, cell, writer.root, plan_raw, digest(nonce))
        intent_path, receipt_path = grant_paths(claim['stage'], cell['id'])
        writer(intent_path, encode(intent))
        for path in (claim['stage'] + '-claim.json', intent_path):
            owned.append(OwnedFile(writer.root / path, code='source_invalid'))
        require(owned[0].raw == encode(claim) and owned[1].raw == encode(intent), 'source_invalid')
        return dict(intent=intent, nonce=nonce, writer=writer, receipt_path=receipt_path,
                    checks=tuple(checks), owned=owned, used=False)
    except BaseException:
        for item in owned:
            item.close()
        raise
    finally:
        controller.close()


def verify_gate(stream, claim, *, intent=None, receipt_path=None):
    """Admit a creator-owned pipe and hold its controller through worker dispatch."""
    require(type(claim) is dict and claim.get('version') == VERSION + '-claim-v2'
            and type(intent) is dict and receipt_path is not None, 'source_invalid')
    controller, receipt = None, None
    try:
        controller = ProcessIdentity(claim['controller_pid'],
                                     created=claim['controller_created_100ns'])
        server, client = pipe_owners(stream)
        require(server == client == controller.pid and controller.pid != os.getpid(),
                'source_invalid')
        worker = ProcessIdentity(os.getpid())
        try:
            worker_created = worker.created
        finally:
            worker.close()
        raw = stream.read(32)
        require(type(raw) is bytes and len(raw) == 32 and digest(raw) == intent['nonce_sha256'],
                'source_invalid')
        ready = dict(version=VERSION + '-worker-ready-v1', cell_id=intent['cell_id'],
            intent_sha256=digest(encode(intent)), worker_pid=os.getpid(),
            worker_created_100ns=worker_created, pipe_server_pid=server, pipe_client_pid=client)
        sys.stderr.buffer.write(GRANT_PREFIX + encode(ready))
        sys.stderr.buffer.flush()
        require(stream.read(1) == b'G', 'source_invalid')
        controller.check()
        receipt = OwnedFile(receipt_path, code='source_invalid')
        observed = json.loads(receipt.raw)
        expected = dict(intent, version=VERSION + '-worker-grant-v1',
            intent_sha256=digest(encode(intent)), worker_pid=os.getpid(),
            worker_created_100ns=worker_created, pipe_server_pid=server, pipe_client_pid=client,
            job_member=True, consumed=True)
        require(set(observed) == set(expected) | {'redirector_pid', 'redirector_created_100ns'}
                and all(type(observed[key]) is type(value) and observed[key] == value
                        for key, value in expected.items())
                and encode(observed) == receipt.raw, 'source_invalid')
        require(observed['redirector_pid'] in (os.getpid(), os.getppid()), 'source_invalid')
        redirector = ProcessIdentity(observed['redirector_pid'],
                                     created=observed['redirector_created_100ns'])
        redirector.close()
        return controller, receipt
    except BaseException:
        for item in (receipt, controller):
            if item is not None:
                item.close()
        raise


def worker_entry(args, source, reader, authority):
    # Full tracked authority/source admission happened in main. Only working-tree
    # ownership is delegated, after the native controller's one-use grant.
    stage = 'qualify' if args.cell == 'qualification' else 'run'
    owned = []

    def read_owned(relative):
        item = OwnedFile(args.run_root / relative, code='source_invalid')
        owned.append(item)
        return item.raw

    try:
        claim = reader.parse_json(read_owned(stage + '-claim.json'))
        runtimes = reader.parse_json(read_owned('runtimes.json'))
        versions = ((3, 11, 15), (3, 14, 6))
        require(sys.version_info[:3] in versions, 'source_invalid')
        slot = versions.index(sys.version_info[:3])
        prescribed = ('D:/Pontius-tools/py311/Scripts/python.exe',
                      'D:/Pontius/.venv/Scripts/python.exe')[slot]
        authorized = authority['runtimes'][slot]
        reader.shape(authorized, 'id version executable source_root')
        require(authorized['id'] == ('3.11', '3.14')[slot]
                and authorized['version'] == '.'.join(map(str, sys.version_info[:3]))
                and Path(authorized['executable']) == Path(prescribed)
                and Path(authorized['source_root']) == args.source_root, 'source_invalid')
        require(type(runtimes) is list and len(runtimes) == 2, 'source_invalid')
        runtime = runtimes[slot]
        require(all(runtime[key] == authorized[key] for key in ('id', 'version'))
                and all(Path(runtime[key]) == Path(authorized[key])
                        for key in ('executable', 'source_root'))
                and Path(runtime['executable']) == Path(sys.executable)
                and Path(runtime['resolved_executable']) == Path(sys._base_executable),
                'source_invalid')
        config = reader.parse_json(read_owned(f'admission/{runtime["id"]}-venv.json'))
        own_runtime(runtime, config, owned)
        manifest = read_owned(f'admission/{runtime["id"]}-source.manifest')
        require(manifest == source.manifest and digest(manifest) == runtime['source_sha256'],
                'source_invalid')
        if stage == 'qualify':
            plan_raw = None
            cell = dict(id='qualification', kind='qualification', runtime=runtime['id'],
                        recipe_sha256=authority['recipe_sha256'])
        else:
            plan_raw = read_owned('plan.json')
            plan = reader.parse_json(plan_raw)
            reader.validate_plan(plan)
            qualified = reader.parse_json(read_owned('qualified.json'))
            require(qualified['source_commit'] == source.commit
                    and qualified['plan_sha256'] == digest(plan_raw), 'source_invalid')
            cells = [cell for cell in plan['cells'] if cell['id'] == args.cell]
            require(len(cells) == 1 and cells[0]['runtime'] == runtime['id'], 'input_invalid')
            cell = cells[0]
            intent = reader.parse_json(read_owned(f'cells/{args.cell}/intent.json'))
            expected = dict(version=VERSION + '-intent-v1', cell_id=cell['id'], cell=cell,
                source_sha256=runtime['source_sha256'],
                protocol_sha256=runtime['protocol_sha256'],
                population_sha256=plan['population_sha256'])
            require(encode(intent) == encode(expected), 'input_invalid')
        intent_path, receipt_path = grant_paths(stage, args.cell)
        intent = reader.parse_json(read_owned(intent_path))
        expected = grant_intent(claim, source, runtime, cell, args.run_root, plan_raw,
                                intent.get('nonce_sha256'))
        require(encode(intent) == encode(expected), 'source_invalid')
        source.check()
        for item in owned:
            item.check()
        lease = verify_gate(sys.stdin.buffer, claim, intent=intent,
                            receipt_path=args.run_root / receipt_path)
        owned.extend(lease)
        source.check()
        for item in owned:
            item.check()
        writer = Writer(args.run_root)
        if stage == 'qualify':
            population = load_tool('population', args.source_root, source.captured)
            for index, item in enumerate(runtimes):
                population._runtime(item, index)
            stage_sample('ready')
            manifest = population.build_population({'version': VERSION + '-recipe-v1'}, writer)
            writer('population.json', encode(manifest))
            writer('plan.json', encode(population.freeze_plan(manifest, runtimes)))
            stage_sample('final')
            return 0
        if cell['kind'] == 'session':
            require(cell['parameters']['diagnostic'] is True, 'input_invalid')
            params = cell['parameters']
            return diagnostic(args.source_root, ['--session', params['session_path'],
                '--blueprint', params['blueprint_path'], '--session-id', params['session_id'],
                '--strategy', params['strategy'], '--auto', '--format', 'json'],
                args.run_root / f'cells/{args.cell}/profile.json')
        stage_sample('ready')
        population = load_tool('population', args.source_root, source.captured)
        measure = load_tool('measure', args.source_root, source.captured)
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
    finally:
        closing = []
        for item in reversed(owned):
            try:
                item.close()
            except BaseException as error:
                closing.append('interrupted' if isinstance(error, KeyboardInterrupt)
                               else 'cleanup_failed')
        if closing:
            active = sys.exception()
            if active is None:
                raise Refusal(closing[0], secondary=closing[1:])
            active.secondary = (*getattr(active, 'secondary', ()), *closing)


def qualify(args, source, reader, sources, authority):
    regular(args.run_root.parent, directory=True)
    args.run_root.mkdir(exist_ok=False)
    writer, owned = Writer(args.run_root), []
    started = time.perf_counter_ns()
    try:
        claim = claim_stage(args.run_root, writer, 'qualify', source, source.captured[AUTHORITY])
        runtimes = freeze_runtimes(authority, args.run_root, sources, writer, owned)
        writer('runtimes.json', encode(runtimes))
        runtime = runtimes[0]
        worker_source = next(s for s in sources if s.root == Path(runtime['source_root']))
        argv = [runtime['executable'], '-B', '-P', str(worker_source.root / ADDITIONS[0]),
                'worker', '--source-root', str(worker_source.root),
                '--run-root', str(args.run_root),
                '--authorization', runtime['authorization'], '--cell', 'qualification']
        environment = runtime_environment(worker_source.root,
                                          args.run_root / 'temporary' / runtime['id'])
        writer('qualification-intent.json', encode(dict(
            argv=argv, recipe_sha256=authority['recipe_sha256'])))
        writer('qualification-environment.json', encode(environment))
        owned.extend(OwnedFile(args.run_root / ref['path']) for ref in writer.references)
        cell = dict(id='qualification', kind='qualification', runtime=runtime['id'],
                    recipe_sha256=authority['recipe_sha256'])
        remaining = 1_800_000_000_000 - (time.perf_counter_ns() - started)
        require(remaining > 0, 'budget_exhausted')
        gate = prepare_worker_grant(claim, worker_source, runtime, cell, writer,
                                    checks=(*sources, *owned))
        result = supervise(argv, worker_source.root, environment, timeout_ns=remaining,
                           worker=True, gate=gate)
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
    writer, owned, slots, failures, missing = Writer(args.run_root), [], [], [], []
    stage_claim = claim_stage(args.run_root, writer, 'run', source, source.captured[AUTHORITY])
    stop, started, finished, active = None, None, None, None
    validator, attempts, plan, retention_deadline = None, {}, None, None
    admitted_cells = None

    def retention_time():
        require(retention_deadline is None or time.monotonic() < retention_deadline,
                'budget_exhausted')

    def failure(error, phase, slot=None):
        nonlocal stop
        cause = ('interrupted' if isinstance(error, KeyboardInterrupt) else
                 getattr(error, 'code', 'worker_failed'))
        if type(cause) is not str or cause not in reader.CAUSES:
            cause = 'worker_failed'
        if stop is None:
            stop = cause
        failures.append(dict(cell_id=None if slot is None else slot['cell']['id'],
            phase=phase, cause=cause, exception_type=type(error).__name__,
            detail=str(error)[:512]))
        if slot is not None and slot['published'] is None:
            record = slot['result']
            if record['cause'] is None:
                record['cause'] = cause
            elif cause != record['cause']:
                record['secondary'].append(cause)
            record['secondary'].extend(code for code in getattr(error, 'secondary', ())
                                       if code in reader.CAUSES)
            if record['status'] != 'unattempted' or slot is active:
                record['status'] = ('interrupted' if record['cause'] == 'interrupted'
                                    else 'failed')
        return cause

    def existing(name, raw):
        path = args.run_root / name
        if not path.exists():
            return None
        with OwnedFile(path) as item:
            require(item.raw == raw, 'input_invalid')
        return dict(path=name, sha256=digest(raw), bytes=len(raw))

    def retain(name, raw, phase, slot=None):
        # One initial publication and at most one recovery, never an execution retry.
        try:
            retention_time()
            reference = existing(name, raw)
            if reference is not None:
                return reference
        except (Exception, KeyboardInterrupt) as error:
            failure(error, phase, slot)
        while attempts.get(name, 0) < 2:
            attempts[name] = attempts.get(name, 0) + 1
            try:
                retention_time()
                return existing(name, raw) or writer(name, raw)
            except (Exception, KeyboardInterrupt) as error:
                failure(error, phase, slot)
                try:
                    reconciled = existing(name, raw)
                    if reconciled is not None:
                        return reconciled
                except (Exception, KeyboardInterrupt) as conflict:
                    failure(conflict, phase, slot)
                    break
        if name not in missing:
            missing.append(name)
        return None

    def retain_inputs(slot):
        prefix = 'cells/' + slot['cell']['id'] + '/'
        for name, value in (('intent', slot['intent']), ('environment', slot['environment'])):
            retain(prefix + name + '.json', encode(value), name, slot)

    def adopt_native(slot):
        nonlocal started, finished, stop
        native = slot['native']
        if not native or slot.get('native_adopted'):
            return
        record = slot['result']
        if native['redirector_pid'] is not None:
            if started is None:
                started = native['launch_ns']
            finished = native['launch_ns'] + native['outer_ns']
        causes = ([native['cause']] if native['cause'] is not None else [])
        causes += native['secondary']
        record.update(outer_ns=native['outer_ns'], exit_code=native['exit_code'],
            cleanup=dict(native['cleanup']), secondary=list(causes[1:]))
        record['captures']['truncated'] = native['truncated']
        if causes:
            record.update(cause=causes[0], status=(
                'interrupted' if causes[0] == 'interrupted' else 'failed'))
            if stop is None:
                stop = causes[0]
        slot['native_adopted'] = True

    def retain_native(slot):
        native = slot['native']
        if not native:
            return
        prefix = 'cells/' + slot['cell']['id'] + '/'
        retain(prefix + 'supervision.json', encode(
            {key: value for key, value in native.items() if key not in ('stdout', 'stderr')}),
            'capture', slot)
        for name in ('stdout', 'stderr'):
            slot['result']['captures'][name] = retain(
                prefix + name + '.bin', native[name], 'capture', slot)

    def commit_result(slot):
        nonlocal stop
        prefix = 'cells/' + slot['cell']['id'] + '/'
        record = slot['result']
        if record['status'] == 'unattempted':
            record['cause'] = stop or 'worker_failed'
        while slot.get('result_attempts', 0) < 2:
            slot['result_attempts'] = slot.get('result_attempts', 0) + 1
            raw = None
            try:
                retention_time()
                record['files'] = []
                for path in sorted((args.run_root / prefix).iterdir()):
                    retention_time()
                    if path.is_file() and path.name != 'result.json':
                        with OwnedFile(path) as item:
                            record['files'].append(dict(
                                path=path.relative_to(args.run_root).as_posix(),
                                sha256=digest(item.raw), bytes=len(item.raw)))
                record['secondary'] = list(dict.fromkeys(record['secondary']))
                reader.validate_result(record)
                raw = encode(record)
                retention_time()
                reference = existing(prefix + 'result.json', raw) or writer(
                    prefix + 'result.json', raw)
                slot['published'] = dict(reference=reference, record=reader.parse_json(raw))
                return
            except (Exception, KeyboardInterrupt) as error:
                # Reconcile an already committed exact result before recording a
                # late run-level fault; its closed cell census stays immutable.
                if raw is not None:
                    try:
                        reference = existing(prefix + 'result.json', raw)
                        if reference is not None:
                            slot['published'] = dict(reference=reference,
                                                     record=reader.parse_json(raw))
                    except (Exception, KeyboardInterrupt) as conflict:
                        failure(conflict, 'result', slot)
                failure(error, 'result', slot)
                if slot['published'] is not None:
                    return
        missing.append(prefix + 'result.json')

    def make_slot(cell):
        runtime = next(r for r in plan['runtimes'] if r['id'] == cell['runtime'])
        return dict(cell=cell, runtime=runtime, native={}, published=None,
            environment=runtime_environment(Path(runtime['source_root']),
                args.run_root / 'temporary' / runtime['id']),
            intent=dict(version=VERSION + '-intent-v1', cell_id=cell['id'], cell=cell,
                source_sha256=runtime['source_sha256'],
                protocol_sha256=runtime['protocol_sha256'],
                population_sha256=plan['population_sha256']),
            result=dict(version=VERSION + '-result-v1', cell_id=cell['id'],
                status='unattempted', cause=None, secondary=[], observations={}, files=[],
                outer_ns=None, exit_code=None, cleanup=dict(verified=False, active=None),
                captures=dict(stdout=None, stderr=None, truncated=False)))

    try:
        qualified_file = OwnedFile(args.run_root / 'qualified.json')
        owned.append(qualified_file)
        qualified = reader.parse_json(qualified_file.raw)
        require(qualified['source_commit'] == source.commit, 'source_invalid')
        reader.file_ref(qualified['manifest'])
        qualification_file = OwnedFile(args.run_root / qualified['manifest']['path'])
        owned.append(qualification_file)
        require(digest(qualification_file.raw) == qualified['manifest']['sha256'])
        for reference in reader.parse_json(qualification_file.raw)['files']:
            reader.file_ref(reference)
            item = OwnedFile(args.run_root / reference['path'])
            owned.append(item)
            require(digest(item.raw) == reference['sha256'] and len(item.raw) == reference['bytes'])
        plan_raw = (args.run_root / 'plan.json').read_bytes()
        require(digest(plan_raw) == qualified['plan_sha256'])
        plan = reader.parse_json(plan_raw)
        reader.validate_plan(plan)
        population = reader.parse_json((args.run_root / 'population.json').read_bytes())
        require(digest(encode(population)) == plan['population_sha256'])
        host = load_tool('host', source.root, source.captured)
        validation_source = host.Source(source.root)
        validator = (host, validation_source, validation_source.load())
        population_tool = load_tool('population', source.root, source.captured)
        require(encode(plan) == encode(population_tool.freeze_plan(population, plan['runtimes'])))
        # This is the admitted-plan boundary. Allocate the complete ordered census
        # before any intent publication, runtime admission or child launch.
        admitted_cells = plan['cells']
        for cell in admitted_cells:
            slots.append(make_slot(cell))
        for active in slots:
            retain_inputs(active)
            if stop is not None:
                break
        if stop is None:
            owned.extend(OwnedFile(args.run_root / ref['path']) for ref in writer.references)
            active = slots[0] if slots else None
            admit_run_runtimes(plan, args.run_root, source, sources, reader, owned)
        for active in slots:
            if stop is not None:
                break
            cell, runtime, record = active['cell'], active['runtime'], active['result']
            direct = cell['kind'] != 'session'
            runtime_source = next(item for item in sources
                                  if item.root == Path(runtime['source_root']))
            checked = (*sources, *owned)
            now = time.perf_counter_ns()
            remaining = 3_600_000_000_000 - (0 if started is None else now - started)
            require(remaining > 0, 'budget_exhausted')
            gate = (prepare_worker_grant(stage_claim, runtime_source, runtime, cell, writer,
                        plan_raw=plan_raw, checks=checked)
                    if direct or cell['parameters'].get('diagnostic') else b'')
            if not gate:
                for item in checked:
                    item.check()
            deadline = None if started is None else started + 3_600_000_000_000
            require(deadline is None or time.perf_counter_ns() < deadline, 'budget_exhausted')
            supervise(cell['argv'], runtime_source.root, active['environment'],
                timeout_ns=remaining, deadline_ns=deadline, worker=direct, gate=gate,
                outcome=active['native'])
            adopt_native(active)
            retain_native(active)
            for item in checked:
                item.check()
            native = active['native']
            if not direct:
                params = cell['parameters']
                ordinal = params['deal'] * 72 + params['seat'] * 12 + params['lineup'] * 2
                ordinal += int(params['strategy'] == 'baseline-rules-v1')
                chunk = args.run_root / f'population/query-{ordinal // 128:03d}.jsonl'
                reference = reader.parse_json(chunk.read_bytes().splitlines()[ordinal % 128])
                if native['cause'] is not None:
                    artifact = next(a for a in population['artifacts'] if a['size'] == cell['size'])
                    binding = reader.session_binding(Path(params['session_path']).read_bytes(),
                        validator[1].commit, validator[1].child_manifest,
                        artifact['file']['sha256'], artifact['source_sha256'], params['strategy'])
                    facts = reader.failed_session_facts(native['stdout'],
                        cell, dict(trajectory=reference, binding=binding),
                        truncated=native['truncated'])
                    for fact in facts['facts']:
                        original = fact['record']
                        validator[2].trace._validate_timing(
                            original['failure']['timing'], label='retained workload failure')
                        if original['decision'] is not None:
                            validator[2].provider_codec.validate_decision(original['decision'])
                    record['failed_session_facts'] = facts
            require(native['cause'] is None, native['cause'] or 'worker_failed')
            require(native['cleanup']['verified'] and not native['secondary'], 'cleanup_failed')
            if direct:
                observations = reader.parse_json((args.run_root /
                    f'cells/{cell["id"]}/observations.json').read_bytes())
                observations['memory_samples'] = native['samples']
            else:
                events = []
                if cell['parameters']['diagnostic']:
                    profile = args.run_root / f'cells/{cell["id"]}/profile.json'
                    events = reader.parse_json(profile.read_bytes())
                    events = [dict(event, ns=event['ns'] - native['launch_ns']) for event in events]
                    reader.reduce_spans(events, native['outer_ns'])
                observations = session_observations(native['stdout'], cell, reference,
                    source.root, reader, events, validator)
            reader.validate_observations(observations, cell)
            if record['cause'] is None:
                record.update(status='completed', observations=observations)
            commit_result(active)
            active = None
    except (Exception, KeyboardInterrupt) as error:
        if active is not None:
            adopt_native(active)
        failure(error, 'execution' if active is not None and active['native'] else 'admission',
                active)
        if active is not None and active['native']:
            for item in (*sources, *owned):
                try:
                    item.check()
                except (Exception, KeyboardInterrupt) as changed:
                    failure(changed, 'source', active)
    finally:
        # Finalization can retry evidence publication once, never a cell. A bounded
        # retention interval cannot guarantee storage survives recurrent faults.
        retention_deadline = time.monotonic() + 300
        active = None
        if admitted_cells is not None:
            for cell in admitted_cells[len(slots):]:
                try:
                    retention_time()
                    slots.append(make_slot(cell))
                except (Exception, KeyboardInterrupt) as error:
                    failure(error, 'admission')
                    missing.extend('cells/' + item['id'] + '/result.json'
                                   for item in admitted_cells[len(slots):])
                    break
        for slot in slots:
            if slot['published'] is not None:
                continue
            if time.monotonic() >= retention_deadline:
                missing.append('cells/' + slot['cell']['id'] + '/result.json')
                continue
            try:
                retain_inputs(slot)
                retain_native(slot)
                commit_result(slot)
            except (Exception, KeyboardInterrupt) as error:
                failure(error, 'result', slot)
                missing.append('cells/' + slot['cell']['id'] + '/result.json')
        for item in (*owned, *sources):
            try:
                if hasattr(item, 'close'):
                    item.close()
            except (Exception, KeyboardInterrupt) as error:
                failure(error, 'close')
        terminal = dict(version=VERSION + '-terminal-v1', cells=[
            dict(cell_id=slot['cell']['id'], status=slot['published']['record']['status'])
            for slot in slots if slot['published'] is not None])
        if slots:
            retain('terminal.json', encode(terminal), 'terminal')
        retain('run-envelope.json', encode(dict(started_ns=started, finished_ns=finished,
                                               stop=stop)), 'envelope')
        retention = dict(version=VERSION + '-retention-v1', complete=bool(slots) and not missing,
                         failures=failures, missing=list(dict.fromkeys(missing)))
        prior_failures = len(failures)
        retain('retention.json', encode(retention), 'envelope')
        if len(failures) != prior_failures:
            try:
                stage_refusal(writer, reader, 'retention-final-refusal.json',
                              Refusal(failures[-1]['cause']))
            except (Exception, KeyboardInterrupt):
                sys.stderr.write('workload retention incomplete\n')
        try:
            file_manifest(args.run_root, writer, 'manifest.json', check=retention_time)
        except (Exception, KeyboardInterrupt) as error:
            failure(error, 'manifest')
            # Earlier canonical evidence remains immutable. If even this receipt
            # cannot be saved, stderr and nonzero exit are the remaining evidence.
            try:
                stage_refusal(writer, reader, 'retention-final-refusal.json', error)
            except (Exception, KeyboardInterrupt):
                sys.stderr.write('workload retention incomplete\n')
    return 0 if stop is None and slots and not missing else 1


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
        ('GetProcessTimes', [ctypes.c_void_p] * 5, ctypes.c_int),
        ('GetFileType', [ctypes.c_void_p], ctypes.c_ulong),
        ('GetNamedPipeServerProcessId', [ctypes.c_void_p, ctypes.c_void_p], ctypes.c_int),
        ('GetNamedPipeClientProcessId', [ctypes.c_void_p, ctypes.c_void_p], ctypes.c_int),
        ('IsProcessInJob', [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p], ctypes.c_int),
        ('K32GetProcessMemoryInfo', [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_ulong],
         ctypes.c_int),
    ):
        function = getattr(api, name)
        function.argtypes, function.restype = args, result
    return api


def process_created(handle):
    times = (ctypes.c_ulonglong * 4)()
    require(process_api().GetProcessTimes(handle, *(
        ctypes.byref(times, index * 8) for index in range(4))), 'source_invalid')
    require(times[0] > 0, 'source_invalid')
    return int(times[0])


class ProcessIdentity:
    """Pin one live kernel process object; a later PID lookup cannot replace it."""
    def __init__(self, pid, *, created=None, job=None):
        require(type(pid) is int and pid > 0, 'source_invalid')
        self.api, self.pid, self.handle = process_api(), pid, None
        try:
            self.handle = self.api.OpenProcess(0x101000, False, pid)
            require(self.handle, 'source_invalid')
            self.created = process_created(self.handle)
            require(created is None or type(created) is int and created == self.created,
                    'source_invalid')
            self.check()
            if job is not None:
                member = ctypes.c_int()
                require(self.api.IsProcessInJob(self.handle, job.handle, ctypes.byref(member))
                        and member.value == 1, 'source_invalid')
        except BaseException:
            self.close()
            raise

    def check(self):
        require(self.api.WaitForSingleObject(self.handle, 0) == 258
                and process_created(self.handle) == self.created, 'source_invalid')

    def close(self):
        if self.handle:
            handle, self.handle = self.handle, None
            require(self.api.CloseHandle(handle), 'cleanup_failed')


def pipe_owners(stream):
    api, handle = process_api(), msvcrt.get_osfhandle(stream.fileno())
    require(api.GetFileType(handle) == 3, 'source_invalid')
    owners = []
    for name in ('GetNamedPipeServerProcessId', 'GetNamedPipeClientProcessId'):
        value = ctypes.c_ulong()
        require(getattr(api, name)(handle, ctypes.byref(value)), 'source_invalid')
        owners.append(int(value.value))
    return tuple(owners)


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
              stderr_limit=256 * 1024, stop=None, worker=False, gate=None, outcome=None,
              deadline_ns=None):
    """Own a suspended worker before it executes; fault seams only request real cleanup."""
    job, process, sampler, cause = None, None, None, None
    secondary, samples, threads, streams = [], [], [], [bytearray(), bytearray()]
    overflow, messages = threading.Event(), queue.Queue()
    truncated, exit_code, active = False, None, None
    worker_failure, worker_grant, grant_process = None, None, None
    reader, result = None, None
    launched = time.perf_counter_ns()
    deadline = launched

    def budget():
        require(time.perf_counter_ns() < deadline, 'budget_exhausted')

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
                if worker or gate:
                    pending.extend(chunk)
                    while b'\n' in pending:
                        line, _, tail = pending.partition(b'\n')
                        pending = bytearray(tail)
                        if (index == 0 and worker or index == 1 and
                                line.startswith((CONTROL_PREFIX, GRANT_PREFIX))):
                            messages.put((index, bytes(line)))
                    if len(pending) > 8192:
                        overflow.set()
        except OSError:
            messages.put(None)

    def failure_message(raw):
        nonlocal cause, worker_failure
        message = reader.parse_json(raw[len(CONTROL_PREFIX):])
        require(type(message) is dict and set(message) == {'version', 'cell_id', 'cause',
                'secondary', 'exception_type'} and message['version'] ==
                VERSION + '-worker-failure-v1' and type(message['cell_id']) is str
                and 0 < len(message['cell_id']) <= 128
                and type(message['cause']) is str and message['cause'] in reader.CAUSES
                and type(message['secondary']) is list
                and all(type(code) is str and code in reader.CAUSES
                        for code in message['secondary'])
                and len(set(message['secondary'])) == len(message['secondary'])
                and type(message['exception_type']) is str
                and 0 < len(message['exception_type']) <= 128
                and worker_failure is None, 'worker_failed')
        require(not gate or message['cell_id'] == gate['intent']['cell_id'], 'source_invalid')
        worker_failure = message
        if cause in (None, 'worker_failed'):
            cause = message['cause']
        elif cause != message['cause']:
            secondary.append(message['cause'])
        secondary.extend(message['secondary'])

    def grant_message(raw):
        nonlocal worker_grant, grant_process
        require(gate and not gate['used'] and grant_process is None, 'source_invalid')
        message, intent = reader.parse_json(raw[len(GRANT_PREFIX):]), gate['intent']
        expected = dict(version=VERSION + '-worker-ready-v1', cell_id=intent['cell_id'],
            intent_sha256=digest(encode(intent)), pipe_server_pid=intent['controller_pid'],
            pipe_client_pid=intent['controller_pid'])
        require(type(message) is dict and set(message) == set(expected) | {
                'worker_pid', 'worker_created_100ns'} and all(
                type(message[key]) is type(value) and message[key] == value
                for key, value in expected.items()), 'source_invalid')
        require(message['worker_pid'] != os.getpid(), 'source_invalid')
        grant_process = ProcessIdentity(message['worker_pid'],
            created=message['worker_created_100ns'], job=job)
        require(pipe_owners(process.stdin) == (os.getpid(), os.getpid()), 'source_invalid')
        # These checks own the full parent working tree and all admitted inputs.
        # The child is blocked at its gate throughout this final pre-release check.
        for item in (*gate['checks'], *gate['owned']):
            item.check()
        grant_process.check()
        budget()
        receipt = dict(intent, version=VERSION + '-worker-grant-v1',
            intent_sha256=digest(encode(intent)), redirector_pid=process.pid,
            redirector_created_100ns=process_created(int(process._handle)),
            worker_pid=grant_process.pid, worker_created_100ns=grant_process.created,
            pipe_server_pid=os.getpid(), pipe_client_pid=os.getpid(),
            job_member=True, consumed=True)
        # Consuming the local capability precedes durable publication and release.
        # A publication failure cannot make this capability reusable.
        gate['used'] = True
        try:
            gate['writer'](gate['receipt_path'], encode(receipt))
        except BaseException:
            # Publication can finish before an interruption is delivered. Preserve
            # that exact consumed receipt without replacing the originating failure.
            try:
                path = Path(intent['run_root']) / gate['receipt_path']
                if path.exists():
                    with OwnedFile(path, code='source_invalid') as published:
                        require(published.raw == encode(receipt), 'source_invalid')
                        worker_grant = receipt
            except BaseException as error:
                secondary.append('interrupted' if isinstance(error, KeyboardInterrupt)
                                 else 'source_invalid')
            raise
        worker_grant = receipt
        budget()
        process.stdin.write(b'G')
        process.stdin.flush()

    try:
        require(type(timeout_ns) is int and timeout_ns > 0 and
                (deadline_ns is None or type(deadline_ns) is int), 'input_invalid')
        deadline = launched + timeout_ns
        if deadline_ns is not None:
            deadline = min(deadline, deadline_ns)
        require(outcome is None or type(outcome) is dict, 'input_invalid')
        require(not gate or type(gate) is dict and set(gate) == {
                'intent', 'nonce', 'writer', 'receipt_path', 'checks', 'owned', 'used'}
                and gate['used'] is False and type(gate['nonce']) is bytes
                and len(gate['nonce']) == 32 and digest(gate['nonce']) ==
                gate['intent']['nonce_sha256'], 'source_invalid')
        if gate:
            controller = ProcessIdentity(os.getpid(),
                created=gate['intent']['controller_created_100ns'])
            try:
                require(gate['intent']['controller_pid'] == os.getpid(), 'source_invalid')
            finally:
                controller.close()
        host = load_tool('host', root)
        reader = load_tool('report', root)
        job = host.Job()
        budget()
        launched = time.perf_counter_ns()
        process = subprocess.Popen(argv, cwd=root, env=environment, stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=0x08000004)
        job.assign(process)
        for index, (pipe, limit) in enumerate(((process.stdout, stdout_limit),
                                               (process.stderr, stderr_limit))):
            thread = threading.Thread(target=capture, args=(pipe, index, limit), daemon=True)
            thread.start()
            threads.append(thread)
        budget()
        job.resume(process)
        if gate:
            budget()
            process.stdin.write(gate['nonce'])
            process.stdin.flush()
        while True:
            elapsed = time.perf_counter_ns() - launched
            if overflow.is_set():
                truncated, cause = True, 'capture_limit'
                break
            if time.perf_counter_ns() >= deadline:
                cause = 'budget_exhausted'
                break
            if stop is not None:
                cause = stop(elapsed, tuple(samples))
                if cause is not None:
                    break
            while not messages.empty():
                item = messages.get_nowait()
                require(item is not None, 'worker_failed')
                index, raw = item
                if index == 1:
                    if raw.startswith(GRANT_PREFIX):
                        grant_message(raw)
                    else:
                        failure_message(raw)
                    continue
                message = json.loads(raw)
                require(type(message) is dict and set(message) == {'stage', 'pid'}
                        and message['stage'] in ('idle', 'read', 'decode', 'prepare', 'first',
                                                'ready', 'final'), 'worker_failed')
                require(not gate or worker_grant is not None
                        and message['pid'] == grant_process.pid, 'source_invalid')
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
                budget()
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
        if gate and worker_grant is None and cause is None:
            cause = 'source_invalid'
    except KeyboardInterrupt:
        cause = 'interrupted'
    except Exception as error:
        cause = getattr(error, 'code', 'worker_failed')
        secondary.extend(getattr(error, 'secondary', ()))
    finally:
        cleanup_start = time.perf_counter_ns()

        def cleanup(operation):
            try:
                return operation()
            except BaseException as error:
                secondary.append('interrupted' if isinstance(error, KeyboardInterrupt)
                                 else 'cleanup_failed')
                secondary.extend(getattr(error, 'secondary', ()))
                return None

        def exit_wait_ms():
            # After a stop, the existing bounded cleanup allowance still applies.
            if cause is not None or secondary:
                return 10000
            return min(10000, max(0, (deadline - time.perf_counter_ns()) // 1_000_000))

        if job is not None:
            if cause is None and not secondary:
                # A signalled redirector and the job's active census need not settle
                # in the same instant. Observe descendants before judging completion.
                verification_end = min(deadline, cleanup_start + 10_000_000_000)
                active = cleanup(job.active)
                while active and time.perf_counter_ns() < verification_end:
                    cleanup(lambda: time.sleep(0.01))
                    active = cleanup(job.active)
                if active:
                    cause = 'worker_failed'
            if cause is not None or secondary or active != 0:
                cleanup(job.terminate)
        # Creation confers ownership even when assignment never succeeds. A Job
        # census cannot certify this root's termination: kill and reap it directly.
        if process is not None:
            def reap():
                # Popen.kill can cache an exit code while Windows termination is
                # still completing, and Popen.wait then skips its native wait.
                # Observe the held process object itself before claiming exit.
                require(process_api().WaitForSingleObject(
                    int(process._handle), exit_wait_ms()) == 0,
                        'cleanup_failed')
                return process.wait(timeout=0)

            if process.poll() is None and (cause is not None or secondary):
                cleanup(process.kill)
            exit_code = cleanup(reap)
            if exit_code is None:
                if job is not None:
                    cleanup(job.terminate)
                cleanup(process.kill)
                exit_code = cleanup(reap)
        if job is not None:
            job_empty_deadline = time.monotonic() + 10
            active = cleanup(job.active)
            while active != 0 and time.monotonic() < job_empty_deadline:
                cleanup(lambda: time.sleep(0.01))
                active = cleanup(job.active)
            if active != 0:
                secondary.append('cleanup_failed')
        else:
            active = 0
        for thread in threads:
            cleanup(lambda: thread.join(timeout=5))
            if thread.is_alive():
                secondary.append('cleanup_failed')
        # Stderr can become readable immediately after poll observes exit. Keep
        # its typed originating failure even when it arrives during finalization.
        while not messages.empty():
            item = messages.get_nowait()
            if item is not None and item[0] == 1:
                if item[1].startswith(CONTROL_PREFIX):
                    cleanup(lambda: failure_message(item[1]))
                else:
                    secondary.append('source_invalid')
        if overflow.is_set():
            truncated = True
            if cause is None:
                cause = 'capture_limit'
            elif cause != 'capture_limit':
                secondary.append('capture_limit')
        # Job active-process accounting can settle before the held worker process
        # object is signalled. Certify this exact base worker, not a later PID lookup.
        for item in (sampler, grant_process):
            if item is not None:
                cleanup(lambda: require(item.api.WaitForSingleObject(
                    item.handle, exit_wait_ms()) == 0,
                                        'cleanup_failed'))
        outer_ns = time.perf_counter_ns() - launched
        for item in (sampler, grant_process, job):
            if item is not None:
                cleanup(item.close)
        if process is not None:
            for stream in (process.stdin, process.stdout, process.stderr):
                if stream is not None:
                    cleanup(stream.close)
        if type(gate) is dict:
            for item in gate.get('owned', ()):
                cleanup(item.close)
        cleanup_verified = not secondary and active == 0
        if process is not None and launched + outer_ns >= deadline:
            if cause is None:
                cause = 'budget_exhausted'
            elif cause != 'budget_exhausted':
                secondary.append('budget_exhausted')
        result = {'cause': cause, 'secondary': list(dict.fromkeys(secondary)),
            'exit_code': exit_code, 'stdout': bytes(streams[0]), 'stderr': bytes(streams[1]),
            'truncated': truncated or overflow.is_set(), 'samples': samples,
            'redirector_pid': process.pid if process is not None else None,
            'launch_ns': launched, 'outer_ns': outer_ns,
            'cleanup_ns': time.perf_counter_ns() - cleanup_start,
            'worker_failure': worker_failure, 'worker_grant': worker_grant,
            'cleanup': {'verified': cleanup_verified, 'active': active}}
        if type(outcome) is dict:
            outcome.clear()
            outcome.update(result)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('qualify', 'run', 'read', 'worker'))
    for name in ('source-root', 'run-root', 'authorization'):
        parser.add_argument('--' + name, required=name != 'authorization', type=Path)
    parser.add_argument('--cell')
    sources, failures = [], []
    args, reader, outcome = None, None, 1
    try:
        args = parser.parse_args(argv)
        require(os.name == 'nt' and sys.implementation.name == 'cpython'
                and sys.dont_write_bytecode and sys.flags.safe_path, 'source_invalid')
        require(args.source_root.is_absolute() and args.run_root.is_absolute()
                and args.source_root == Path(__file__).absolute().parents[1])
        require((args.cell is not None) == (args.mode == 'worker'))
        source = FrozenSource(args.source_root, delegated=args.mode == 'worker')
        sources.append(source)
        reader = load_tool('report', source.root, source.captured)
        if args.mode == 'read':
            require(args.authorization is None and args.cell is None)
            report = reader.read_run(args.run_root)
            sys.stdout.buffer.write(encode(report))
            outcome = 0
        else:
            require(args.authorization is not None and args.authorization.is_absolute(),
                    'source_invalid')
            authority = admit_authority(source, args.authorization, args.run_root, reader)
            if args.mode == 'worker':
                outcome = worker_entry(args, source, reader, authority)
            else:
                require(sys.version_info[:3] == (3, 11, 15)
                        and Path(sys.executable) == Path(
                            'D:/Pontius-tools/py311/Scripts/python.exe'), 'source_invalid')
                action = qualify if args.mode == 'qualify' else run
                outcome = action(args, source, reader, sources, authority)
    except SystemExit as error:
        outcome = int(error.code)
    except (Exception, KeyboardInterrupt) as error:
        failures.append(error)
    finally:
        for source in sources:
            try:
                source.close()
            except (Exception, KeyboardInterrupt) as error:
                failures.append(error)
    if failures:
        codes = []
        for index, error in enumerate(failures):
            code = ('interrupted' if isinstance(error, KeyboardInterrupt) else
                    getattr(error, 'code', 'input_invalid' if index == 0 else 'cleanup_failed'))
            codes.extend((code, *getattr(error, 'secondary', ())))
        if reader is not None:
            codes = [code if type(code) is str and code in reader.CAUSES else 'worker_failed'
                     for code in codes]
        if args is not None and args.mode == 'worker' and args.cell is not None:
            failure = dict(version=VERSION + '-worker-failure-v1', cell_id=args.cell,
                cause=codes[0], secondary=list(dict.fromkeys(codes[1:])),
                exception_type=type(failures[0]).__name__)
            raw = CONTROL_PREFIX + encode(failure)
            # write accepts the usual stderr capture used by admission controls.
            sys.stderr.write(raw.decode('utf-8'))
            sys.stderr.flush()
        else:
            sys.stderr.write(str(codes[0]) + '\n')
        return 1
    return outcome


if __name__ == '__main__':
    raise SystemExit(main())
