"""Independent Python 3.14 recorder for a hash-bound evaluation invocation."""
from __future__ import annotations

import hashlib
import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import signal
import stat
import subprocess
import sys
import tempfile
import threading
import time


def require(condition, message):
    if not condition:
        raise ValueError(message)


def document(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, 'duplicate JSON member')
            result[key] = value
        return result

    def constant(token):
        raise ValueError('nonfinite JSON constant: ' + token)

    return json.loads(raw, object_pairs_hook=pairs, parse_constant=constant)


def is_link(path):
    info = path.lstat()
    return stat.S_ISLNK(info.st_mode) or bool(
        getattr(info, 'st_file_attributes', 0) & getattr(stat, 'FILE_ATTRIBUTE_REPARSE_POINT', 0))


def file_identity(path):
    require(not is_link(path) and path.is_file(), 'expected an owned regular file: ' + str(path))
    digest, size = hashlib.sha256(), 0
    with path.open('rb') as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
            size += len(chunk)
    return dict(bytes=size, sha256=digest.hexdigest())


def inventory(directory):
    """Enumerate completely or raise; never publish a successful partial traversal."""
    rows = []

    def walk(parent):
        require(not is_link(parent), 'linked inventory directory')
        with os.scandir(parent) as entries:
            paths = sorted((Path(entry.path) for entry in entries), key=lambda p: p.name)
        for path in paths:
            require(not is_link(path), 'linked inventory entry')
            if path.is_dir():
                walk(path)
            else:
                rows.append(dict(path=path.relative_to(directory).as_posix(),
                                 **file_identity(path)))

    walk(directory)
    require(rows, 'empty run inventory')
    return sorted(rows, key=lambda row: row['path'])


def run_directories(root):
    directory = root / 'experiments/results/runs'
    require(not is_link(directory), 'linked run container')
    with os.scandir(directory) as entries:
        paths = [Path(entry.path) for entry in entries]
    require(all(not is_link(p) and p.is_dir() for p in paths), 'unexpected run-container entry')
    return {p.name for p in paths}


def attribute(root, before, commit, prior_runs):
    """Require one appended row and exactly its new run; preserve row bytes verbatim."""
    current = (root / 'execution_journal.jsonl').read_bytes()
    require(current.startswith(before), 'existing journal bytes changed')
    tail = current[len(before):]
    require(tail.endswith(b'\n') and len(tail.splitlines()) == 1, 'expected one new journal row')
    row = document(tail)
    require(type(row) is dict and row.get('source_commit') == commit
            and row.get('source_verified') is True, 'journal source identity mismatch')
    output = row.get('output')
    require(type(output) is str, 'journal output missing')
    relative = Path(output)
    require(not relative.is_absolute() and len(relative.parts) == 5
            and relative.parts[:3] == ('experiments', 'results', 'runs')
            and relative.name == 'result.json' and '..' not in relative.parts,
            'journal output is not a run result')
    path = root / relative
    run = path.parent
    require(run_directories(root) == prior_runs | {run.name} and run.name not in prior_runs,
            'missing, old or unattributed run directory')
    require(file_identity(path)['sha256'] == row.get('output_sha256'), 'result digest mismatch')
    require(file_identity(run / 'runtimes.json')['sha256'] == row.get('runtimes_sha256'),
            'runtime digest mismatch')
    return tail, run


def write_new(path, raw):
    with path.open('xb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())


def exit_status(child_exit, complete):
    return child_exit if child_exit not in (None, 0) else (0 if complete else 99)


def encoded(value):
    return (json.dumps(value, sort_keys=True, allow_nan=False) + '\n').encode('utf-8')


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def digest(value, length=64):
    return (type(value) is str and len(value) == length
            and all(c in '0123456789abcdef' for c in value))


def absolute(value):
    require(type(value) is str and Path(value).is_absolute(), 'absolute path required')
    return Path(value)


class Refusal(ValueError):
    def __init__(self, message, code=2):
        super().__init__(message)
        self.code = code


def git_output(config, *args):
    return subprocess.run([config['git'], '--no-replace-objects', '-c',
                           'safe.directory=' + config['root'], '-C', config['root'], *args],
                          check=True, capture_output=True, timeout=30).stdout


def launch_environment():
    system = os.environ.get('SystemRoot') or os.environ.get('SYSTEMROOT')
    require(system and Path(system).is_dir(), 'SystemRoot/SYSTEMROOT directory required')
    environment = dict(SystemRoot=system, PYTHONDONTWRITEBYTECODE='1')
    for key in ('TEMP', 'TMP'):
        value = os.environ.get(key)
        require(value and Path(value).is_absolute() and Path(value).is_dir(), key + ' required')
        # Check real temporary-file creation, not just ACL-derived access flags.
        with tempfile.TemporaryFile(dir=value):
            pass
        environment[key] = value
    return environment


def check_binding(item):
    require(type(item) is dict and set(item) == {'path', 'sha256'}
            and digest(item['sha256']), 'invalid file binding')
    path = absolute(item['path'])
    require(file_identity(path)['sha256'] == item['sha256'], 'bound bytes differ: ' + str(path))
    return path


def preflight(binding_path, expected_hash):
    require(sys.version_info[:2] == (3, 14), 'runner requires Python 3.14')
    require(digest(expected_hash), 'launch binding SHA-256 required')
    raw = binding_path.read_bytes()
    require(0 < len(raw) <= 1024 * 1024 and sha(raw) == expected_hash, 'launch binding mismatch')
    config = document(raw)
    keys = {'version', 'root', 'retained_root', 'mode', 'source_commit', 'python', 'git',
            'plan', 'records', 'authorization', 'baseline', 'runner_sha256'}
    require(type(config) is dict and set(config) == keys
            and config['version'] == 'pontius-eval-launch-v1', 'invalid launch binding')
    require(config['mode'] in ('retained', 'rehearsal') and digest(config['source_commit'], 40),
            'invalid mode or source commit')
    require(config['runner_sha256'] == file_identity(Path(__file__))['sha256'], 'runner changed')
    root, retained = absolute(config['root']), absolute(config['retained_root'])
    records = absolute(config['records'])
    require(root.is_dir() and not is_link(root), 'owned checkout required')
    require(not records.resolve().is_relative_to((root/'experiments/results/runs').resolve()),
            'recorder output must be outside child run storage')
    if records.exists() and any(records.iterdir()):
        raise Refusal('record directory already used; claim is never retried', 97)
    for key in ('python', 'git'):
        file_identity(absolute(config[key]))
    environment = launch_environment()
    environment.update(PONTIUS_GIT=config['git'], GIT_CONFIG_COUNT='1',
                       GIT_CONFIG_KEY_0='safe.directory', GIT_CONFIG_VALUE_0=str(root))
    require(git_output(config, 'rev-parse', 'HEAD').decode().strip() == config['source_commit'],
            'HEAD differs from bound source')
    if config['mode'] == 'rehearsal':
        require(root.resolve() != retained.resolve(), 'rehearsal is the retained checkout')
        require(git_output(config, 'rev-parse', '--abbrev-ref', 'HEAD').strip() == b'HEAD',
                'rehearsal requires a detached checkout')
    else:
        require(root.resolve() == retained.resolve(), 'retained root mismatch')
        authorization = document(absolute(config['authorization']).read_bytes())
        require(type(authorization) is dict
                and set(authorization) == {'binding_sha256', 'controller_text'}
                and authorization['binding_sha256'] == expected_hash
                and type(authorization['controller_text']) is str
                and authorization['controller_text'].strip(), 'authorization binding missing')
    require(not git_output(config, 'status', '--porcelain', '--', 'src', 'tools', 'tests',
                           'pyproject.toml', 'uv.lock', '.gitattributes', '.github').strip(),
            'source scope is dirty')
    file_identity(root/'tools/v0a_eval_panel.py')
    plan_path = check_binding(config['plan'])
    require(plan_path.resolve().is_relative_to(root.resolve()), 'plan leaves execution checkout')
    plan = document(plan_path.read_bytes())
    require(type(plan) is dict and plan.get('phase') in
            ('capacity', 'preflight', 'solve', 'export', 'agreement'), 'invalid phase')
    resource = plan['resource']
    require(type(resource) is dict and set(resource) == {'seconds', 'memory_mib'}
            and type(resource['seconds']) in (int, float)
            and math.isfinite(resource['seconds']) and resource['seconds'] > 0
            and type(resource['memory_mib']) is int and resource['memory_mib'] > 0,
            'finite positive child resource envelope required')
    runtime = subprocess.run([config['python'], '-I', '-B', '-c',
                              'import sys; print(".".join(map(str, sys.version_info[:3])))'],
                             check=True, capture_output=True, env=environment, timeout=15)
    require(runtime.stdout.decode().strip() == plan['runtime']['python']
            and plan['runtime']['python'].startswith('3.14.'), 'child Python version differs')
    for group in ('inputs', 'prerequisites'):
        entries = plan.get(group, {})
        require(type(entries) is dict, 'input bindings must be an object')
        for item in entries.values():
            check_binding(item)
    baseline = config['baseline']
    require(type(baseline) is dict and set(baseline) == {'journal_sha256', 'run_directories'}
            and digest(baseline['journal_sha256']), 'invalid baseline')
    journal = (root/'execution_journal.jsonl').read_bytes()
    require((not journal or journal.endswith(b'\n')) and sha(journal) == baseline['journal_sha256'],
            'journal differs from prepared baseline')
    prior_runs = run_directories(root)
    require(sorted(prior_runs) == baseline['run_directories'], 'run directories changed')
    return config, plan, journal, prior_runs, environment


@contextmanager
def defer_interrupts():
    """The child receives console signals; the recorder waits to preserve its final evidence."""
    received, previous = [], {}
    deferred = True

    def handle(number, frame):
        received.append(number)
        if not deferred:
            raise KeyboardInterrupt

    def stop_deferring():
        nonlocal deferred
        deferred = False

    if threading.current_thread() is threading.main_thread():
        for name in ('SIGINT', 'SIGBREAK'):
            if signum := getattr(signal, name, None):
                previous[signum] = signal.signal(signum, handle)
    try:
        yield received, stop_deferring
    finally:
        for number, handler in previous.items():
            signal.signal(number, handler)


def launch(config, environment, records, report):
    command = [config['python'], '-B', '-P', '-W', 'error::ResourceWarning',
               str(Path(config['root'])/'tools/v0a_eval_panel.py'), 'run',
               '--reviewed-commit', config['source_commit'], '--plan', config['plan']['path']]
    with (records/'stdout.json').open('xb') as out, (records/'stderr.txt').open('xb') as err:
        with subprocess.Popen(command, cwd=config['root'], env=environment,
                              stdout=out, stderr=err) as child:
            report['child_exit'] = code = child.wait()
        out.flush()
        err.flush()
        os.fsync(out.fileno())
        os.fsync(err.fileno())
    return code


def run(binding_path, expected_hash, *, check_only=False):
    try:
        config, plan, before, prior_runs, environment = preflight(binding_path, expected_hash)
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as error:
        print('REFUSED: ' + str(error), file=sys.stderr)
        return getattr(error, 'code', 2)
    if check_only:
        print(json.dumps(dict(state='preflight', phase=plan['phase'],
                              binding_sha256=expected_hash)))
        return 0
    records, root = Path(config['records']), Path(config['root'])
    report = dict(state='claimed', phase=plan['phase'], mode=config['mode'],
                  binding_sha256=expected_hash, plan_sha256=config['plan']['sha256'],
                  source_commit=config['source_commit'], resource=plan['resource'],
                  started_utc=datetime.now(timezone.utc).isoformat(), child_exit=None,
                  errors=[], evidence={})
    with defer_interrupts() as (interrupted, stop_deferring):
        try:
            records.mkdir(parents=True, exist_ok=True)
            (records/'claim.d').mkdir()
        except OSError as error:
            print('CLAIM REFUSED: ' + str(error), file=sys.stderr)
            return 97
        try:
            write_new(records/'claim.d/claim.json', encoded(report))
            report['state'] = 'launching'
            write_new(records/'start.json', encoded(report))
        except (OSError, ValueError) as error:
            print('START RECORD FAILED; claim consumed: ' + str(error), file=sys.stderr)
            return 98
        started = time.perf_counter()
        try:
            require(not interrupted, 'interrupted before child creation')
            report['child_exit'] = launch(config, environment, records, report)
            report['state'] = 'exited'
        except (OSError, ValueError, subprocess.SubprocessError) as error:
            report['errors'].append('launch/capture: ' + str(error))
        report['wall_seconds'] = time.perf_counter() - started
        try:
            for name in ('stdout.json', 'stderr.txt'):
                report['evidence'][name] = file_identity(records/name)
            row, directory = attribute(root, before, config['source_commit'], prior_runs)
            write_new(records/'journal-row.jsonl', row)
            report['evidence']['journal-row.jsonl'] = file_identity(records/'journal-row.jsonl')
            rows = inventory(directory)
            write_new(records/'inventory.json', encoded(dict(run=directory.name, files=rows)))
            report['evidence']['inventory.json'] = file_identity(records/'inventory.json')
            report['run_directory'] = str(directory)
            result = document((directory/'result.json').read_bytes())
            require(result.get('phase') == plan['phase']
                    and result.get('plan_sha256') == config['plan']['sha256'],
                    'result belongs to a different phase/plan')
            if report['child_exit'] == 0:
                require(result.get('status') == 'completed'
                        and result.get('cleanup_verified') is True
                        and result.get('resource_state_verified') is True,
                        'successful child lacks completion/cleanup evidence')
                if plan['phase'] in ('solve', 'export', 'agreement'):
                    require(result.get('phase_complete') is True, 'phase incomplete')
        except (OSError, ValueError, KeyError, TypeError) as error:
            report['errors'].append('evidence: ' + str(error))
        try:
            # Signals after this boundary must unwind publication, not update a stale snapshot.
            stop_deferring()
            report['signals'] = interrupted.copy()
            if interrupted:
                report['errors'].append('recorder interrupted; no complete claim issued')
            complete = report['child_exit'] is not None and not report['errors']
            report['evidence_complete'] = complete
            report['state'] = (
                ('verified' if report['child_exit'] == 0 else 'failed')
                if complete else 'incomplete')
            report['exit'] = exit_status(report['child_exit'], complete)
            report['finished_utc'] = datetime.now(timezone.utc).isoformat()
            write_new(records/'outcome.json', encoded(report))
            print(json.dumps(dict(state=report['state'], exit=report['exit'],
                                  records=str(records))))
            return report['exit']
        except KeyboardInterrupt:
            print('FINALIZATION INTERRUPTED; claim consumed; signals: ' + str(interrupted),
                  file=sys.stderr)
            return exit_status(report['child_exit'], False)
        except (OSError, ValueError) as error:
            print('FINAL RECORD FAILED; claim consumed: ' + str(error), file=sys.stderr)
            return exit_status(report['child_exit'], False)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--binding', type=Path, required=True)
    parser.add_argument('--sha256', required=True)
    parser.add_argument('--check', action='store_true', help='preflight only; no claim or child')
    args = parser.parse_args(argv)
    return run(args.binding, args.sha256, check_only=args.check)


if __name__ == '__main__':
    raise SystemExit(main())
