"""Bounded, retained paired correctness runner; no scientific execution authority."""
from __future__ import annotations
import argparse
import ctypes
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import threading
import time
import types

BASE = 'e043f81ecec3ac16128720b42c3312bb41a4ed67'
OLD = tuple('tools/' + n + '.py' for n in ('v0a_rehearsal_driver', 'v0a_hand_adapter',
    'v0a_event_adapter', 'v0a_table_host', 'v0a_table_session', 'v0a_seeded_deals'))
NEW = ('tools/v0a_evaluation.py', 'tools/v0a_evaluation_contract.py')
BLUEPRINT = 'tests/fixtures/table_host/empty_blueprint.json'
ALIASES = ('_pontius_evaluation_contract', '_pontius_evaluation_dealer', '_pontius_evaluation_host')
KEEP_ENV = ('SystemRoot', 'WINDIR', 'SystemDrive', 'COMSPEC', 'USERPROFILE',
            'APPDATA', 'LOCALAPPDATA')
PREFIX = 'pontius-v0a-evaluation-'
clock_ns = time.monotonic_ns


def require(condition, code='source_invalid'):
    if not condition:
        raise ValueError(code)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def encode(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True,
                       allow_nan=False) + '\n').encode('ascii')


def checked_path(path, directory=False, d_local=True):
    require(path.is_absolute() and len(path.drive) == 2 and '..' not in path.parts
            and (not d_local or path.drive.upper() == 'D:'))
    for current in (*path.parents, path):
        info = current.lstat()
        require(not info.st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT
                and (stat.S_ISDIR(info.st_mode) if current != path or directory
                     else stat.S_ISREG(info.st_mode)))
    return path


def identity(info):
    return info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns


def directory_ids(path):
    return tuple((p.stat().st_dev, p.stat().st_ino) for p in path.parents)


def read_stable(path, cap=16777216):
    checked_path(path, d_local=False)
    before, ancestors = identity(path.stat()), directory_ids(path)
    require(before[2] <= cap, 'input_invalid')
    with path.open('rb') as stream:
        require(identity(os.fstat(stream.fileno())) == before, 'input_invalid')
        raw = stream.read(cap + 1)
        require(identity(os.fstat(stream.fileno())) == before, 'input_invalid')
    checked_path(path, d_local=False)
    require(identity(path.stat()) == before and len(raw) == before[2], 'input_invalid')
    require(directory_ids(path) == ancestors, 'input_invalid')
    return raw, (before, ancestors)


def create_file(path, raw):
    checked_path(path.parent, True, False)
    with path.open('xb') as stream:
        require(stream.write(raw) == len(raw), 'output_failed')
        stream.flush()
        os.fsync(stream.fileno())
        token = identity(os.fstat(stream.fileno())), directory_ids(path)
    require(read_stable(path) == (raw, token), 'output_failed')
    return raw, token


class SourceBinding:
    def command(self, *args, content=None):
        require(read_stable(self.git) == self.captured[self.git])
        result = subprocess.run([str(self.git), '--no-replace-objects', '--no-optional-locks',
            '-C', str(self.repo), *args], input=content, env=self.env,
            capture_output=True, timeout=30)
        require(result.returncode == 0)
        return result.stdout

    def inventory(self, commit):
        rows = self.command('ls-tree', '-r', '-z', commit, '--', 'src/pontius', *OLD,
                            BLUEPRINT, *NEW)
        result = {}
        for row in rows.split(b'\0'):
            if row:
                meta, path = row.split(b'\t', 1)
                mode, kind, oid = meta.split()
                require(mode in (b'100644', b'100755') and kind == b'blob')
                result[path.decode('utf-8')] = oid.decode('ascii')
        return result

    def check(self):
        require(self.command('rev-parse', '--verify', 'HEAD^{commit}').decode().strip()
                == self.commit)
        require(not any(n == 'pontius' or n.startswith('pontius.') for n in sys.modules))
        actual, dirs = set(), set()
        for parent, directories, files in os.walk(self.repo / 'src/pontius', followlinks=False):
            for name in directories:
                path = checked_path(Path(parent) / name, True)
                dirs.add(path.relative_to(self.repo).as_posix())
            actual.update((Path(parent) / n).relative_to(self.repo).as_posix() for n in files)
        require(actual == {p for p in self.raw if p.startswith('src/pontius/')})
        require(dirs == {p.as_posix() for name in actual for p in Path(name).parents
                         if p.as_posix().startswith('src/pontius/')})
        for path, captured in self.captured.items():
            require(read_stable(path) == captured)
        for alias, module in getattr(self, 'modules', {}).items():
            require(sys.modules.get(alias) is module and module.__file__ == str(
                self.repo / (NEW[1], OLD[5], OLD[3])[ALIASES.index(alias)]))


def admit_source(repo):
    require(os.name == 'nt' and sys.implementation.name == 'cpython'
            and sys.version_info >= (3, 11) and sys.flags.safe_path and sys.dont_write_bytecode)
    require(not any(n == 'pontius' or n.startswith('pontius.') or n in ALIASES
                    for n in sys.modules))
    s = SourceBinding()
    s.repo = checked_path(repo, True)
    require(Path(__file__).absolute() == repo / NEW[0] and Path.cwd() == repo)
    s.python = checked_path(Path(sys.executable), d_local=False)
    s.git = checked_path(Path(os.environ.get('PONTIUS_GIT', '')), d_local=False)
    s.captured = {p: read_stable(p) for p in (s.python, s.git)}
    api = ctypes.WinDLL('kernel32', use_last_error=True)
    api.GetBinaryTypeW.argtypes = [ctypes.c_wchar_p, ctypes.POINTER(ctypes.c_ulong)]
    for path in (s.python, s.git):
        kind = ctypes.c_ulong()
        require(api.GetBinaryTypeW(str(path), ctypes.byref(kind)) and kind.value in (0, 6))
    s.env = {k: os.environ[k] for k in KEEP_ENV if k in os.environ}
    s.commit = s.command('rev-parse', '--verify', 'HEAD^{commit}').decode().strip()
    require(re.fullmatch('[0-9a-f]{40}', s.commit))
    old, current = s.inventory(BASE), s.inventory(s.commit)
    require(set(current) == set(old) | set(NEW)
            and all(current[p] == oid for p, oid in old.items()))
    batch = s.command('cat-file', '--batch', content=('\n'.join(current.values())+'\n').encode())
    s.raw, offset = {}, 0
    for name, oid in current.items():
        end = batch.index(b'\n', offset)
        header = batch[offset:end].split()
        require(header[:2] == [oid.encode(), b'blob'] and len(header) == 3)
        size, offset = int(header[2]), end + 1
        s.raw[name] = batch[offset:offset+size]
        offset += size
        require(batch[offset:offset+1] == b'\n')
        offset += 1
    require(offset == len(batch))
    s.captured.update({s.repo / p: read_stable(s.repo / p) for p in s.raw})
    require(all(s.captured[s.repo / p][0] == raw for p, raw in s.raw.items()))
    rows = {p: sha(raw).encode() + b'  ' + p.encode() + b'\n' for p, raw in s.raw.items()}
    s.manifest = sha(b''.join(sorted(rows.values())))
    s.child_manifest = sha(b''.join(sorted(v for p, v in rows.items()
        if p.startswith('src/pontius/') or p in OLD[:3])))
    s.check()
    s.modules = {}
    for alias, path in zip(ALIASES, (NEW[1], OLD[5], OLD[3])):
        module = types.ModuleType(alias)
        module.__file__ = str(repo / path)
        sys.modules[alias] = module
        s.modules[alias] = module
        exec(compile(s.raw[path], module.__file__, 'exec'), module.__dict__)
    s.contract, s.dealer, s.host = (s.modules[n] for n in ALIASES)
    s.check()
    return s


def child_environment(source, temp):
    checked_path(temp, True, False)
    return dict(source.env, TEMP=str(temp), TMP=str(temp), PONTIUS_GIT=str(source.git),
                PYTHONPATH=str(source.repo / 'src'), PYTHONNOUSERSITE='1', PYTHONIOENCODING='utf-8')


def child_argv(binding, paths):
    return [str(binding['source'].python), '-B', '-P', 'tools/v0a_table_session.py',
        '--session', str(paths['input']), '--blueprint', str(binding['source'].repo / BLUEPRINT),
        '--session-id', binding['session_id'], '--strategy', binding['strategy'],
        '--format', 'json', '--auto']


def revalidate(binding):
    binding['source'].check()
    for path, saved in binding['saved'].items():
        require(read_stable(path) == saved, 'input_invalid')


def add_cause(causes, error, phase):
    code = ('interrupted' if isinstance(error, KeyboardInterrupt) else
            getattr(error, 'code', str(error) if isinstance(error, ValueError) else phase))
    for value in (code, *getattr(error, 'secondary', ())):
        if value not in causes:
            causes.append(value)


def run_trial(binding, paths, deadline_ns):
    s, root, started = binding['source'], paths['root'], clock_ns()
    budget = binding['trial_budget_ms'] * 1000000
    trial_deadline = started + budget
    causes, resources, threads, done = [], [], [], [False, False]
    job = process = None
    creation_attempted = False
    launched, cleanup, phase, exit_code = False, True, 'admission', None
    capture_failed = threading.Event()
    def drain(stream, output, cap, index, name):
        size = 0
        try:
            while True:
                raw = os.read(stream.fileno(), 65536)
                if not raw:
                    done[index] = True
                    break
                kept = raw[:max(0, cap-size)]
                require(output.write(kept) == len(kept), 'capture_failed')
                size += len(raw)
                require(size <= cap, name + '_overflow')
        except BaseException as error:
            add_cause(causes, error, 'capture_failed')
            capture_failed.set()
    try:
        require(started + budget + 5000000000 <= deadline_ns, 'budget_insufficient')
        revalidate(binding)
        require(clock_ns() + budget + 5000000000 <= deadline_ns, 'budget_insufficient')
        argv, env = child_argv(binding, paths), child_environment(s, paths['temp'])
        intent = {k: binding[k] for k in ('ordinal', 'pair_index', 'strategy', 'session_id',
            'source_commit', 'source_manifest_sha256', 'request_sha256', 'input_sha256')}
        intent.update(version=PREFIX+'intent-v1', argv=argv, environment=env,
                      intent_ns=clock_ns(), trial_deadline_ns=trial_deadline)
        launched = None
        create_file(root / 'intent.json', encode(intent))
        for name in ('stdout.bin', 'stderr.bin'):
            resources.append((root / name).open('xb'))
        phase = 'containment_failed'
        job = s.host.Job()
        revalidate(binding)
        require(clock_ns() + budget + 5000000000 <= deadline_ns, 'budget_insufficient')
        require(clock_ns() <= trial_deadline, 'trial_timeout')
        phase, creation_attempted = 'launch_failed', True
        process = subprocess.Popen(argv, cwd=s.repo, env=env, stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NO_WINDOW | 4)
        resources.extend((process.stdout, process.stderr))
        phase = 'containment_failed'
        job.assign(process)
        job.resume(process)
        phase = 'launch_record_failed'
        create_file(root / 'launch.json', encode(dict(version=PREFIX+'launch-v1',
            ordinal=binding['ordinal'], pid=process.pid, created_suspended=True,
            assigned=True, resumed=True)))
        launched = True
        for index, (stream, cap, name) in enumerate(((process.stdout, 4194304, 'stdout'),
                                                   (process.stderr, 65536, 'stderr'))):
            thread = threading.Thread(target=drain,
                args=(stream, resources[index], cap, index, name), daemon=True)
            threads.append(thread)
            thread.start()
        phase = 'capture_failed'
        while process.poll() is None or job.active() or not all(done):
            require(not capture_failed.is_set(), causes[0] if causes else 'capture_failed')
            require(clock_ns() <= trial_deadline, 'trial_timeout')
            time.sleep(.005)
        exit_code = process.returncode
    except BaseException as error:
        add_cause(causes, error, phase)
    finally:
        if creation_attempted and process is None:
            cleanup = False
            add_cause(causes, ValueError('cleanup_unknown'), 'cleanup_unknown')
        grace = time.monotonic() + 5
        def attempt(operation):
            nonlocal cleanup
            try:
                operation()
            except BaseException as error:
                cleanup = False
                add_cause(causes, error, 'cleanup_failed')
        if job is not None:
            attempt(job.terminate)
        if process is not None:
            attempt(lambda: process.kill() if process.poll() is None else None)
            attempt(lambda: process.wait(timeout=max(.001, grace-time.monotonic())))
            exit_code = process.returncode
        if job is not None:
            def inactive():
                while job.active():
                    require(time.monotonic() <= grace, 'cleanup_failed')
                    time.sleep(.005)
            attempt(inactive)
            attempt(job.close)
        for thread in threads:
            if thread.ident is not None:
                attempt(lambda: thread.join(timeout=max(.001, grace-time.monotonic())))
                if thread.is_alive():
                    cleanup = False
                    add_cause(causes, ValueError('cleanup_failed'), 'cleanup_failed')
        for stream in resources:
            if not any(t.is_alive() for t in threads):
                if stream in resources[:2]:
                    attempt(stream.flush)
                    attempt(lambda: os.fsync(stream.fileno()))
                attempt(stream.close)
        if process is not None:
            attempt(process._handle.Close)
    stdout, stderr = b'', b''
    try:
        if (root / 'stdout.bin').exists():
            stdout = read_stable(root / 'stdout.bin', 4194304)[0]
        if (root / 'stderr.bin').exists():
            stderr = read_stable(root / 'stderr.bin', 65536)[0]
        revalidate(binding)
        require(clock_ns() <= trial_deadline, 'trial_timeout')
    except BaseException as error:
        add_cause(causes, error, 'validation_failed')
    cleanup = cleanup and not any(c in ('cleanup_failed', 'cleanup_unknown') for c in causes)
    result = s.contract.observe_trial(dict(binding, cleanup_complete=cleanup), stdout, stderr,
                                     exit_code, all(done) and not capture_failed.is_set())
    if clock_ns() > trial_deadline:
        add_cause(causes, ValueError('trial_timeout'), 'trial_timeout')
    if causes:
        result.update(state='interrupted' if 'interrupted' in causes else 'failed',
            report_complete=False, observation_complete=False, net_chips=None,
            failure_reason=causes[0])
    result.update(version=PREFIX+'trial-v1', launched=launched, cleanup_complete=cleanup,
        primary_phase=phase if result['state'] != 'completed' else None,
        secondary_failures=causes[1:], elapsed_ns=clock_ns()-started)
    create_file(root / 'result.json', encode(result))
    return result

TRIAL_FIELDS = ('ordinal pair_index strategy state exit_code capture_complete report_complete '
    'net_chips applied_actions_by_kind baseline_fallback_selections baseline_fallback_applied '
    'legacy_choices unattributed_applied_actions work_cutoff_actions action_deadline_actions '
    'observation_complete action_failures failure_reason hand_failure_codes session_failure_codes '
    'capture_deficiencies stdout_sha256 stderr_sha256')
RESULT_FIELDS = ('version evaluation_id status comparison_complete source_commit '
    'source_manifest_sha256 request_sha256 plan_sha256 planned_pairs completed_pairs '
    'planned_trials completed_trials trials pairs aggregate failure_reason secondary_failures '
    'total_elapsed_ns deadline_met evidentiary')


def exact(value, fields):
    require(type(value) is dict and set(value) == set(fields.split()), 'publication_invalid')


def decode_record(raw):
    require(len(raw) <= 16777216 and raw.count(b'{') + raw.count(b'[') <= 200000,
            'publication_invalid')
    def number(token):
        require(len(token.lstrip('-')) <= 640, 'publication_invalid')
        return int(token)
    value = json.loads(raw, parse_int=number)
    def bounded(v, depth=0):
        require(depth <= 16 and type(v) in (dict, list, str, int, bool, type(None)),
                'publication_invalid')
        if type(v) in (dict, list):
            for child in v.values() if type(v) is dict else v:
                bounded(child, depth+1)
    bounded(value)
    require(encode(value) == raw, 'publication_invalid')
    return value


def integer(value, low=0, high=10**640-1):
    return type(value) is int and low <= value <= high


def verify_completed(root):
    snapshots = {root / name: read_stable(root / name) for name in
                 ('result.json', 'completion.json', 'request.json', 'plan.json')}
    r, c, request, plan = (decode_record(v[0]) for v in snapshots.values())
    exact(r, RESULT_FIELDS)
    exact(c, 'version status result_sha256 result_bytes prepared_elapsed_ns deadline_met')
    result_raw = snapshots[root/'result.json'][0]
    require(c['version'] == PREFIX+'completion-v1' and c['status'] == 'completed'
        and c['deadline_met'] is True and c['result_sha256'] == sha(result_raw)
        and integer(c['result_bytes']) and c['result_bytes'] == len(result_raw)
        and integer(c['prepared_elapsed_ns']), 'publication_invalid')
    require(r['version'] == PREFIX+'result-v1' and r['status'] == 'completed'
        and r['comparison_complete'] is True and r['deadline_met'] is True
        and r['evidentiary'] is False and r['failure_reason'] is None
        and r['secondary_failures'] == []
        and integer(r['total_elapsed_ns'], 0, c['prepared_elapsed_ns']), 'publication_invalid')
    require(type(r['evaluation_id']) is str and re.fullmatch(
        PREFIX+'v1-correctness-[A-Za-z0-9_-]{1,16}', r['evaluation_id']), 'publication_invalid')
    for key, size in (('source_commit', 40), ('source_manifest_sha256', 64),
                      ('request_sha256', 64), ('plan_sha256', 64)):
        require(type(r[key]) is str and re.fullmatch('[0-9a-f]{%d}' % size, r[key]),
                'publication_invalid')
    require(r['request_sha256'] == sha(snapshots[root/'request.json'][0])
        and r['plan_sha256'] == sha(snapshots[root/'plan.json'][0]), 'publication_invalid')
    exact(request, 'version seed deal_count lineups seat_start initial_button '
          'total_budget_ms trial_budget_ms')
    require(len(snapshots[root/'request.json'][0]) <= 4096
        and request['version'] == PREFIX+'request-v1' and type(request['seed']) is str
        and re.fullmatch('[0-9a-f]{64}', request['seed']), 'publication_invalid')
    for key, low, high in (('deal_count', 1, 4), ('seat_start', 0, 5), ('initial_button', 0, 5),
                          ('total_budget_ms', 1, 86400000), ('trial_budget_ms', 1, 3600000)):
        require(integer(request[key], low, high), 'publication_invalid')
    lineups = request['lineups']
    require(request['total_budget_ms'] >= request['trial_budget_ms']+5000
        and type(lineups) is list and 1 <= len(lineups) <= 4 and all(type(l) is list
        and len(l) == 5 and all(type(p) is str and p in
        ('passive', 'fold_to_bet', 'min_raise_once', 'shove_once') for p in l) for l in lineups)
        and len({tuple(l) for l in lineups}) == len(lineups), 'publication_invalid')
    exact(plan, 'version request_sha256 source_commit source_manifest_sha256 '
          'blueprint_artifact_sha256 pairs units')
    require(plan['version'] == PREFIX+'plan-v1' and all(plan[k] == r[k] for k in
        ('request_sha256', 'source_commit', 'source_manifest_sha256'))
        and type(plan['blueprint_artifact_sha256']) is str
        and re.fullmatch('[0-9a-f]{64}', plan['blueprint_artifact_sha256']), 'publication_invalid')
    count = 6*request['deal_count']*len(lineups)
    require(all(type(v) is list for v in (plan['pairs'], plan['units'], r['trials'], r['pairs']))
        and len(plan['pairs']) == len(r['pairs']) == count
        and len(plan['units']) == len(r['trials']) == 2*count
        and all(integer(r[k], n, n) for k, n in (('planned_pairs', count),
        ('completed_pairs', count), ('planned_trials', 2*count), ('completed_trials', 2*count))),
        'publication_invalid')
    for i, (t, u) in enumerate(zip(r['trials'], plan['units']), 1):
        exact(t, TRIAL_FIELDS)
        base = (i-1)%4 in (0, 3)
        strategy = 'baseline-rules-v1' if base else 'blueprint-v1'
        pair = plan['pairs'][(i-1)//2]
        expected = dict(ordinal=i, pair_index=(i-1)//2, strategy=strategy,
            session_id='pontius-v0a-table-session-v%d-correctness-eval-%s-u%03d' %
                (2 if base else 1, r['evaluation_id'].split('correctness-')[1], i),
            input_path=pair['input_path'], input_sha256=pair['input_sha256'])
        require(encode(u) == encode(expected), 'publication_invalid')
        require(integer(t['ordinal'], i, i) and integer(t['pair_index'], (i-1)//2, (i-1)//2)
            and t['strategy'] == strategy and t['state'] == 'completed'
            and t['capture_complete'] is True and t['report_complete'] is True
            and t['observation_complete'] is True and integer(t['exit_code'], 0, 0)
            and integer(t['net_chips'], -200, 1000) and t['failure_reason'] is None
            and all(t[k] == [] for k in ('action_failures', 'hand_failure_codes',
                'session_failure_codes', 'capture_deficiencies')), 'publication_invalid')
        for k in ('stdout_sha256', 'stderr_sha256'):
            require(type(t[k]) is str and re.fullmatch('[0-9a-f]{64}', t[k]), 'publication_invalid')
        for k in ('unattributed_applied_actions', 'work_cutoff_actions', 'action_deadline_actions'):
            require(integer(t[k], 0, 0), 'publication_invalid')
        reasons = ('provider_abstained', 'provider_error', 'provider_invalid')
        for key, choices, applicable in (
            ('applied_actions_by_kind', ('fold', 'check', 'call', 'raise'), True),
            ('baseline_fallback_selections', reasons, base),
            ('baseline_fallback_applied', reasons, base),
            ('legacy_choices', ('table_hit', 'passive_default'), not base)):
            value = t[key]
            require((type(value) is dict and set(value) <= set(choices)
                and all(integer(n, 0, 256) for n in value.values())) if applicable
                else value is None, 'publication_invalid')
        counts = t['baseline_fallback_selections'] if base else t['legacy_choices']
        require((t['baseline_fallback_applied'] == counts if base else True)
            and (sum(counts.values()) <= sum(t['applied_actions_by_kind'].values()) if base else
                 sum(counts.values()) == sum(t['applied_actions_by_kind'].values())),
            'publication_invalid')
    for p, (pair, meta) in enumerate(zip(r['pairs'], plan['pairs'])):
        exact(pair, 'pair_index complete baseline_net_chips blueprint_net_chips delta_chips')
        d, l, rot = p//(6*len(lineups)), (p//6)%len(lineups), p%6
        expected = dict(pair_index=p, deal_index=d, lineup_index=l, rotation=rot,
            controlled_seat=(request['seat_start']+rot)%6, button=(request['initial_button']+d)%6,
            input_path='pairs/p%03d.json' % p, input_sha256=meta['input_sha256'])
        require(encode(meta) == encode(expected) and type(meta['input_sha256']) is str
            and re.fullmatch('[0-9a-f]{64}', meta['input_sha256']), 'publication_invalid')
        arms = {t['strategy']: t['net_chips'] for t in r['trials'][2*p:2*p+2]}
        require(pair['complete'] is True and integer(pair['pair_index'], p, p)
            and all(type(pair[k]) is int for k in
                ('baseline_net_chips', 'blueprint_net_chips', 'delta_chips'))
            and pair['baseline_net_chips'] == arms['baseline-rules-v1']
            and pair['blueprint_net_chips'] == arms['blueprint-v1']
            and pair['delta_chips'] == arms['baseline-rules-v1']-arms['blueprint-v1'],
            'publication_invalid')
    def aggregate(rows):
        b, p = (sum(x[k] for x in rows) for k in ('baseline_net_chips', 'blueprint_net_chips'))
        return dict(baseline_net_chips=b, blueprint_net_chips=p, delta_chips=b-p,
                    mean_delta_numerator=b-p, mean_delta_denominator=len(rows))
    expected = aggregate(r['pairs'])
    for field, name in (('lineup_index', 'by_lineup'), ('controlled_seat', 'by_seat')):
        expected[name] = [dict(aggregate([row for row, meta in zip(r['pairs'], plan['pairs'])
            if meta[field] == value]), **{field: value})
            for value in sorted({p[field] for p in plan['pairs']})]
    require(encode(r['aggregate']) == encode(expected), 'publication_invalid')
    for path, saved in snapshots.items():
        require(read_stable(path) == saved, 'publication_invalid')
    return r

def read_completed(root):
    root = checked_path(Path(root), True, False)
    require(not os.path.lexists(root / '.publication-pending'), 'publication_pending')
    result = verify_completed(root)
    require(not os.path.lexists(root / '.publication-pending'), 'publication_pending')
    return result


def publish(root, result, binding, started, deadline_ns):
    guard = root / '.publication-pending'
    guard.mkdir()
    raw = encode(result)
    binding['saved'][root/'result.json'] = create_file(root/'result.json', raw)
    if not result['comparison_complete']:
        return
    completion = dict(version=PREFIX+'completion-v1', status='completed', result_sha256=sha(raw),
        result_bytes=len(raw), prepared_elapsed_ns=clock_ns()-started, deadline_met=True)
    binding['saved'][root/'completion.json'] = create_file(
        root/'completion.json', encode(completion))
    verify_completed(root)
    revalidate(binding)
    require(clock_ns() <= deadline_ns, 'publication_late')
    guard.rmdir()


def execute(args, source):
    root, request_path = args.output_root, args.request
    require(re.fullmatch(PREFIX+'v1-correctness-[A-Za-z0-9_-]{1,16}', args.evaluation_id),
            'input_invalid')
    checked_path(root.parent, True, False)
    checked_path(request_path, d_local=False)
    require(root.is_absolute() and '..' not in root.parts and all(
        root != p and root not in p.parents and p not in root.parents
        for p in (source.repo, request_path)), 'input_invalid')
    request_raw, request_token = read_stable(request_path, 4096)
    root.mkdir()
    started = clock_ns()
    request = source.contract.decode_request(request_raw)
    deadline = started + request['total_budget_ms']*1000000
    reservation = dict(version=PREFIX+'reservation-v1', evaluation_id=args.evaluation_id,
        request_sha256=sha(request_raw), source_commit=source.commit, started_ns=started,
        deadline_ns=deadline)
    saved = {request_path: (request_raw, request_token)}
    for name, raw in (('reservation.json', encode(reservation)), ('request.json', request_raw)):
        saved[root/name] = create_file(root/name, raw)
    deals = [source.dealer.deal_for_hand(request['seed'], d) for d in range(request['deal_count'])]
    suffix = args.evaluation_id.split('correctness-')[1]
    matrix = source.contract.build_matrix(request, deals, suffix)
    (root / 'pairs').mkdir()
    for pair in matrix['pairs']:
        path = root/pair['input_path']
        saved[path] = create_file(path, pair.pop('input_bytes'))
    plan = dict(version=PREFIX+'plan-v1', request_sha256=sha(request_raw),
        source_commit=source.commit, source_manifest_sha256=source.manifest,
        blueprint_artifact_sha256=sha(source.raw[BLUEPRINT]), **matrix)
    saved[root/'plan.json'] = create_file(root/'plan.json', encode(plan))
    binding = dict(source=source, saved=saved, request_sha256=sha(request_raw),
        source_commit=source.commit, source_manifest_sha256=source.manifest,
        child_source_manifest_sha256=source.child_manifest,
        blueprint_artifact_sha256=plan['blueprint_artifact_sha256'],
        blueprint_sha256='d1a3a1435a6dd736f5977a04dc306f8ed42e415f87301d2331d62bb63dcfe683',
        provider='baseline-rules-v1',
        config_sha256='19850a0224933e3b1a975cb4728f3c850756f2d93e2e7fb0f089876507c62954',
        trial_budget_ms=request['trial_budget_ms'])
    trials, causes = [], []
    for unit in plan['units']:
        pair = plan['pairs'][unit['pair_index']]
        current = dict(binding, **unit, controlled_seat=pair['controlled_seat'],
                       button=pair['button'])
        trial = source.contract.observe_trial(current, b'', b'', None, False)
        trial.update(state='unstarted', failure_reason=None, stdout_sha256=None,
                     stderr_sha256=None, capture_deficiencies=[])
        if not causes:
            try:
                unit_root = root / ('u%03d' % unit['ordinal'])
                unit_root.mkdir()
                (unit_root / 'temp').mkdir()
                data = decode_record(saved[root/unit['input_path']][0])
                table = dict(data, **data.pop('hands')[0], version='pontius-v0a-table-input-v1')
                table.pop('hands', None)
                current['table_input_sha256'] = sha(encode(table))
                outcome = run_trial(current, dict(root=unit_root, input=root/unit['input_path'],
                    temp=unit_root/'temp'), deadline)
                trial = {k: outcome[k] for k in TRIAL_FIELDS.split()}
                if outcome['state'] != 'completed':
                    causes = [outcome['failure_reason'], *outcome['secondary_failures']]
                names = ('intent.json', 'launch.json', 'stdout.bin', 'stderr.bin', 'result.json')
                for name in names:
                    if (unit_root/name).exists():
                        saved[unit_root/name] = read_stable(unit_root/name)
            except BaseException as error:
                add_cause(causes, error, 'trial_failed')
                trial.update(state='interrupted' if 'interrupted' in causes else 'failed',
                             failure_reason=causes[0], report_complete=False,
                             observation_complete=False, net_chips=None)
        trials.append(trial)
    reduced = source.contract.reduce_trials(plan, trials)
    complete = reduced['aggregate'] is not None and not causes
    result = dict(version=PREFIX+'result-v1', evaluation_id=args.evaluation_id,
        status='completed' if complete else 'interrupted' if 'interrupted' in causes else 'failed',
        comparison_complete=complete, source_commit=source.commit,
        source_manifest_sha256=source.manifest, request_sha256=sha(request_raw),
        plan_sha256=sha(saved[root/'plan.json'][0]), planned_pairs=len(plan['pairs']),
        completed_pairs=sum(p['complete'] for p in reduced['pairs']), planned_trials=len(trials),
        completed_trials=sum(t['state'] == 'completed' for t in trials), trials=trials, **reduced,
        failure_reason=causes[0] if causes else None, secondary_failures=causes[1:],
        total_elapsed_ns=clock_ns()-started, deadline_met=clock_ns() <= deadline, evidentiary=False)
    publish(root, result, binding, started, deadline)
    return 0 if complete else 130 if 'interrupted' in causes else 1

def main(argv=None):
    try:
        parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
        parser.add_argument('--request', required=True, type=Path)
        parser.add_argument('--output-root', required=True, type=Path)
        parser.add_argument('--evaluation-id', required=True)
        args = parser.parse_args(argv)
        source = admit_source(Path.cwd())
        return execute(args, source)
    except SystemExit as error:
        return 0 if error.code == 0 else 1
    except KeyboardInterrupt:
        return 130
    except Exception as error:
        os.write(2, ('REFUSED ' + str(error) + '\n').encode('utf-8'))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
