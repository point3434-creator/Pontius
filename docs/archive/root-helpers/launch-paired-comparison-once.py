"""External operator for the exact approved ADR-0511 single comparison."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import threading
import time

packet = Path('D:/Pontius-handoffs/v0a-paired-closure/r001')
root = Path('D:/Pontius/tmp/v0a-paired-evaluation-run-001')
source = root/'source'
output = root/'output'
base = 'bd71f4b11dcc0177283431a4ec468fdc152e7686'
source_tree = '54a257f4f2957696b9d33e7338ce140206a3f578'
python = Path('D:/Pontius-tools/py311/Scripts/python.exe')
git_exe = Path('C:/Program Files/Git/cmd/git.exe')
taskkill = Path(os.environ['SystemRoot'])/'System32/taskkill.exe'
request_hash = 'd772691d85a903b4ac6e734b9aa4eac4f75e6ae0096def7c3c0481807729017e'
env = {k: os.environ[k] for k in ('SystemRoot', 'WINDIR', 'SystemDrive', 'COMSPEC',
    'USERPROFILE', 'APPDATA', 'LOCALAPPDATA') if k in os.environ}
env.update(TEMP=str(root/'process-temp'), TMP=str(root/'process-temp'),
    PONTIUS_GIT=str(git_exe), PYTHONPATH=str(source/'src'),
    PYTHONNOUSERSITE='1', PYTHONIOENCODING='utf-8')


def utc():
    return datetime.now(timezone.utc).isoformat()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def save(path, value):
    raw = value if isinstance(value, bytes) else (json.dumps(value, sort_keys=True,
        indent=2, allow_nan=False)+'\n').encode()
    with path.open('xb') as stream:
        assert stream.write(raw) == len(raw)
        stream.flush()
        os.fsync(stream.fileno())


def regular(path, directory=False):
    for parent in reversed(path.parents):
        info = parent.lstat()
        assert stat.S_ISDIR(info.st_mode) and not info.st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT
    info = path.lstat()
    assert not info.st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT
    assert stat.S_ISDIR(info.st_mode) if directory else stat.S_ISREG(info.st_mode)
    return info


def git(repo, *args, content=None):
    result = subprocess.run([str(git_exe), '--no-replace-objects', '-c',
        f'safe.directory={repo.as_posix()}', '-C', str(repo), *args],
        input=content, capture_output=True, env=env, creationflags=subprocess.CREATE_NO_WINDOW)
    assert result.returncode == 0, ('git_failed', args, result.stderr.decode(errors='replace'))
    return result.stdout


def verify_source():
    assert git(source, 'rev-parse', 'HEAD').decode().strip() == base
    assert git(source, 'rev-parse', 'HEAD^{tree}').decode().strip() == source_tree
    assert not git(source, 'status', '--porcelain')
    entries = []
    for row in git(source, 'ls-tree', '-r', '-z', base).split(b'\0'):
        if row:
            meta, name = row.split(b'\t')
            mode, kind, oid = meta.split()
            assert mode in (b'100644', b'100755') and kind == b'blob'
            entries.append((name.decode(), oid))
    batch = git(source, 'cat-file', '--batch', content=b'\n'.join(oid for _, oid in entries)+b'\n')
    offset, rows, total = 0, [], 0
    for name, oid in entries:
        end = batch.index(b'\n', offset)
        header = batch[offset:end].split()
        assert header[:2] == [oid, b'blob']
        size, offset = int(header[2]), end+1
        raw = batch[offset:offset+size]
        offset += size
        assert batch[offset:offset+1] == b'\n'
        offset += 1
        path = source/name
        regular(path)
        assert path.read_bytes() == raw, name
        rows.append(sha(raw)+'  '+name+'\n')
        total += size
    assert offset == len(batch)
    return dict(commit=base, tree=source_tree, tracked_files=len(entries), tracked_bytes=total,
        full_tracked_manifest_sha256=sha(''.join(sorted(rows)).encode()))


def run_capture(name, argv, show_progress=False, budget_ns=None):
    save(root/(name+'-intent.json'), dict(argv=argv, cwd=str(source), environment=env,
        utc=utc(), source_commit=base, request_sha256=request_hash))
    streams = [(root/(name+'-'+n+'.bin')).open('xb') for n in ('stdout', 'stderr')]
    failed = threading.Event()
    counts = [0, 0]
    errors = []
    process = None
    def drain(pipe, stream, index):
        try:
            while True:
                raw = os.read(pipe.fileno(), 4096)
                if not raw:
                    break
                kept = raw[:max(0, 65536-counts[index])]
                assert stream.write(kept) == len(kept)
                counts[index] += len(raw)
                if counts[index] > 65536:
                    raise RuntimeError('diagnostic_capture_overflow')
        except BaseException as error:
            errors.append(type(error).__name__+': '+str(error))
            failed.set()
    threads = []
    started_utc = utc()
    started = time.monotonic_ns()
    try:
        process = subprocess.Popen(argv, cwd=source, env=env, stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=subprocess.CREATE_NO_WINDOW)
        save(root/(name+'-launch.json'), dict(pid=process.pid, utc=utc()))
        for index, pipe in enumerate((process.stdout, process.stderr)):
            thread = threading.Thread(target=drain, args=(pipe, streams[index], index), daemon=True)
            threads.append(thread)
            thread.start()
        while process.poll() is None:
            if budget_ns is not None and time.monotonic_ns()-started > budget_ns:
                raise TimeoutError('reader_observed_exit_deadline')
            if failed.wait(.05 if budget_ns is not None else 1):
                raise RuntimeError('capture_failed')
            if show_progress and time.monotonic_ns()-last_progress[0] >= 10000000000:
                completed_records = sum((output/f'u{i:03d}'/'result.json').is_file() for i in range(1,49))
                print(json.dumps(dict(progress='comparison', retained_unit_records=completed_records,
                    planned_units=48, parent_elapsed_seconds=round((time.monotonic_ns()-started)/1e9,1))), flush=True)
                last_progress[0] = time.monotonic_ns()
        process.wait()
        ended = time.monotonic_ns()
        if budget_ns is not None and ended-started > budget_ns:
            errors.append('reader_observed_exit_deadline')
    except BaseException as error:
        errors.append(type(error).__name__+': '+str(error))
        if process is not None and process.poll() is None:
            stopped = subprocess.run([str(taskkill), '/PID', str(process.pid), '/T', '/F'],
                capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
            save(root/(name+'-tree-stop.json'), dict(exit=stopped.returncode,
                stdout=stopped.stdout.decode(errors='replace'), stderr=stopped.stderr.decode(errors='replace')))
            process.wait(timeout=10)
        ended = time.monotonic_ns()
    finally:
        for thread in threads:
            thread.join(timeout=5)
        if any(t.is_alive() for t in threads):
            errors.append('capture_cleanup_unknown')
        else:
            for stream in streams:
                stream.flush()
                os.fsync(stream.fileno())
                stream.close()
            if process is not None:
                process.stdout.close()
                process.stderr.close()
    result = dict(argv=argv, started_utc=started_utc, finished_utc=utc(),
        started_monotonic_ns=started, finished_monotonic_ns=ended,
        parent_elapsed_ns=ended-started, pid=process.pid if process else None,
        exit_code=process.returncode if process else None, errors=errors,
        observed_capture_bytes=counts, capture_cap_each=65536)
    save(root/(name+'-receipt.json'), result)
    return result



last_progress = [time.monotonic_ns()]
adoption = json.loads((packet/'adoption-result.json').read_bytes())
assert adoption['status'] == 'COMMITTED_AND_PUSHED'
assert adoption['candidate'] == 'e80b794050a466a3f8115b640b53dca3b51816a7'
save(packet/'comparison-opportunity.json', dict(user_message='lets do it', decision='ADR-0511',
    adoption_commit=adoption['commit'], root=str(root), utc=utc(), opportunities=1))
launched = reader = None
try:
    assert not os.path.lexists(root), 'reserved_root_collision'
    root.mkdir()
    save(root/'approval.json', (packet/'adoption-authorization.json').read_bytes())
    save(root/'supervisor.py', Path(__file__).read_bytes())
    (root/'process-temp').mkdir()
    for path in (python, git_exe, taskkill):
        regular(path)
    request = (packet/'files/docs/architecture/v0a-paired-closure-r001/evaluation-request.json').read_bytes()
    assert len(request) == 351 and sha(request) == request_hash
    save(root/'request.json', request)
    git(Path('D:/Pontius'), 'clone', '--quiet', '--no-hardlinks', '--no-checkout',
        'D:/Pontius', str(source))
    git(source, '-c', 'core.autocrlf=false', 'checkout', '--quiet', '--detach', base)
    identity = verify_source()
    identity['executables'] = {str(p): dict(sha256=sha(p.read_bytes()), bytes=p.stat().st_size)
        for p in (python, git_exe, taskkill)}
    save(root/'source-identity.json', identity)
    probe_code = "import sys,pathlib; assert sys.implementation.name=='cpython'; assert sys.version_info[:3]==(3,11,15); assert sys.flags.safe_path and sys.dont_write_bytecode; assert pathlib.Path.cwd()==pathlib.Path(sys.argv[1]); print(sys.version); print(sys.executable); print(pathlib.Path.cwd())"
    probe = run_capture('preflight', [str(python), '-B', '-P', '-c', probe_code, str(source)])
    assert probe['exit_code'] == 0 and not probe['errors'], 'preflight_failed'
    assert not os.path.lexists(output)
    assert (root/'request.json').read_bytes() == request
    argv = [str(python), '-B', '-P', 'tools/v0a_evaluation.py', '--request',
        'D:/Pontius/tmp/v0a-paired-evaluation-run-001/request.json', '--output-root',
        'D:/Pontius/tmp/v0a-paired-evaluation-run-001/output', '--evaluation-id',
        'pontius-v0a-evaluation-v1-correctness-comparison-001']
    launched = run_capture('wrapper', argv, True)
    assert not launched['errors'], 'wrapper_capture_or_cleanup_failed'
    assert verify_source() == {k:v for k,v in identity.items() if k != 'executables'}
    assert (root/'request.json').read_bytes() == request
    for path in (python, git_exe, taskkill):
        regular(path)
        assert sha(path.read_bytes()) == identity['executables'][str(path)]['sha256']
    files = []
    if output.is_dir():
        for parent, directories, names in os.walk(output, followlinks=False):
            regular(Path(parent), True)
            for name in directories:
                regular(Path(parent)/name, True)
            for name in names:
                path = Path(parent)/name
                regular(path)
                raw = path.read_bytes()
                files.append(dict(path=path.relative_to(output).as_posix(), bytes=len(raw), sha256=sha(raw)))
    save(root/'output-file-inventory.json', files)
    output_bytes = sum(f['bytes'] for f in files)
    assert output_bytes <= 4194304, 'retained_output_cap_exceeded'
    save(root/'output-cap-check.json', dict(bytes=output_bytes, cap=4194304,
        files=len(files), passed=True, scope='post-termination retained output only'))
    companion = (packet/'files/docs/architecture/v0a-paired-closure-r001/operating-contract.md').read_bytes()
    assert sha(companion) == 'ea7aeda249f4e7a3d0dfbd38475c8d8a55d724850ae42332bb9e57fe552f5f8d'
    reader_program = companion.decode().split('```python\n',1)[1].split('```',1)[0]
    reader = run_capture('reader', [str(python), '-B', '-P', '-c', reader_program],
        budget_ns=10000000000)
    assert reader['exit_code'] == 0 and not reader['errors'], 'reader_refused_or_cleanup_unknown'
    assert reader['parent_elapsed_ns'] <= 10000000000, 'reader_late'
    assert all(n <= 65536 for n in reader['observed_capture_bytes']), 'reader_capture_overflow'
    raw_result = (root/'reader-stdout.bin').read_bytes()
    result = json.loads(raw_result)
    assert result['planned_pairs'] == result['completed_pairs'] == 24
    assert result['planned_trials'] == result['completed_trials'] == 48
    assert result['source_commit'] == base and result['request_sha256'] == request_hash
    assert result['comparison_complete'] is True and result['evidentiary'] is False
    save(root/'descriptive-result.json', raw_result)
    units = []
    for i in range(1,49):
        path = output/f'u{i:03d}'/'result.json'
        regular(path)
        raw = path.read_bytes()
        value = json.loads(raw)
        unit = {k:value.get(k) for k in ('ordinal','strategy','state','cleanup_complete',
            'exit_code','failure_reason','secondary_failures','capture_complete')}
        unit.update(result_sha256=sha(raw),elapsed_ns_prefix=value.get('elapsed_ns'))
        assert unit['state'] == 'completed' and unit['cleanup_complete'] is True
        units.append(unit)
    report = dict(status='COMPLETED_DESCRIPTIVE_COMPARISON', source=identity,
        adoption_commit=adoption['commit'], request_sha256=request_hash,
        wrapper=launched, reader=reader, units=units,
        planned_trials=48, completed_trials=48, planned_pairs=24, completed_pairs=24,
        descriptive_result_sha256=sha(raw_result), output_files=len(files), output_bytes=output_bytes,
        output_inventory_sha256=sha((root/'output-file-inventory.json').read_bytes()),
        opportunity_consumed=True, lane_budget_exhausted=True, successor_authorized=False,
        standing='Finite descriptive arithmetic only; no strength, selection or tuning claim',
        unknown=['peak process-tree memory','peak disk','action latency distribution'],
        next_required='Written architecture checkpoint and explicit park-or-continue ruling')
    save(root/'comparison-report.json', report)
    save(packet/'comparison-disposition.json', dict(status=report['status'], retained_root=str(root),
        report_sha256=sha((root/'comparison-report.json').read_bytes()),
        opportunity_consumed=True,lane_budget_exhausted=True,raw_evidence_uploaded=False))
    print(json.dumps(dict(status=report['status'],completed_trials=48,completed_pairs=24,
        wrapper_exit=launched['exit_code'],wrapper_seconds=launched['parent_elapsed_ns']/1e9,
        reader_exit=reader['exit_code'],reader_seconds=reader['parent_elapsed_ns']/1e9,
        output_files=len(files),output_bytes=output_bytes,
        report=str(root/'comparison-report.json'))),flush=True)
except BaseException as error:
    record = dict(status='INCOMPLETE', error_type=type(error).__name__, reason=str(error),
        opportunity_consumed=True,lane_budget_exhausted=True,successor_authorized=False,
        utc=utc(),root=str(root),wrapper=launched,reader=reader,
        next_required='Written architecture checkpoint and explicit park-or-continue ruling')
    save(packet/'comparison-incomplete.json', record)
    if root.is_dir() and not os.path.lexists(root/'comparison-incomplete.json'):
        save(root/'comparison-incomplete.json',record)
    print(json.dumps(dict(status='INCOMPLETE',error_type=type(error).__name__,reason=str(error),
        retained_root=str(root),opportunity_consumed=True)),flush=True)
    raise
