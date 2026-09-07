"""Run only the three sealed evaluator suites at their fixed historical source."""
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

BASE_COMMIT = '363c9fb669e19a30375537ee5e92ea338a840a2d'
BASE_TREE = '10cc82ff78a84ef901242b2f69540f6a74ec498b'
SUITES = {'runner': ('tests/test_v0a_evaluation_runner.py', 28),
          'boundary': ('tests/test_v0a_evaluation_boundary.py', 19),
          'v2': ('tests/test_v0a_evaluation_v2.py', 8)}
TEST_HASHES = (
    '9fa3adcd5b350bdcfccfaba251999579e8a37d9d2d63bc7d8789c982ffd3774a',
    '4a7e323c021c1dace35345782873d8ac2a302eeb6bb7b00df7b9d3445c5f980c',
    '76121d42cb8646ea5d47e9f5076cec646a0ea0558c20921ec5b148aac93210cd')


class HistoryRefusal(ValueError):
    """Historical source, launch or result could not be established."""


def require(condition, reason='source_invalid'):
    if not condition:
        raise HistoryRefusal(reason)


def checked_path(path, directory=False, d_local=False):
    require(isinstance(path, Path) and path.is_absolute() and len(path.drive) == 2
            and '..' not in path.parts and (not d_local or path.drive.upper() == 'D:'),
            'input_invalid')
    for item in (*path.parents, path):
        info = item.lstat()
        require(not info.st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT
                and (stat.S_ISDIR(info.st_mode) if item != path or directory
                     else stat.S_ISREG(info.st_mode)), 'input_invalid')
    return path


def native(path):
    checked_path(path)
    api = ctypes.WinDLL('kernel32', use_last_error=True)
    api.GetBinaryTypeW.argtypes = [ctypes.c_wchar_p, ctypes.POINTER(ctypes.c_ulong)]
    kind = ctypes.c_ulong()
    require(api.GetBinaryTypeW(str(path), ctypes.byref(kind)) and kind.value in (0, 6),
            'input_invalid')
    return path


def environment(source, temp):
    env = {name: os.environ[name] for name in ('SystemRoot', 'WINDIR', 'SystemDrive',
        'COMSPEC', 'USERPROFILE', 'APPDATA', 'LOCALAPPDATA') if name in os.environ}
    env.update(TEMP=str(temp), TMP=str(temp), PYTHONPATH=str(source/'src'),
        PYTHONNOUSERSITE='1', PYTHONIOENCODING='utf-8',
        PONTIUS_GIT=str(native(Path(os.environ.get('PONTIUS_GIT', '')))),
        GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull, GIT_ATTR_NOSYSTEM='1')
    return env


def git(repo, env, *args, content=None):
    result = subprocess.run([env['PONTIUS_GIT'], '--no-replace-objects', '--no-optional-locks',
        '-c', 'core.autocrlf=false', '-c', 'core.longpaths=true', '-C', str(repo), *args],
        input=content,
        env=env, capture_output=True, timeout=120)
    require(result.returncode == 0)
    return result.stdout


def checked_history(source, env):
    """Compare actual checkout bytes and index modes/paths with the complete pinned tree."""
    try:
        checked_path(source, True, True)
        require(git(source, env, 'rev-parse', 'HEAD').decode().strip() == BASE_COMMIT)
        require(git(source, env, 'rev-parse', 'HEAD^{tree}').decode().strip() == BASE_TREE)
        rows = git(source, env, 'ls-tree', '-r', '-z', BASE_COMMIT).split(b'\0')
        expected = {}
        for row in rows:
            if row:
                metadata, path = row.split(b'\t', 1)
                mode, kind, oid = metadata.split()
                require(mode in (b'100644', b'100755') and kind == b'blob')
                expected[path.decode()] = (mode, oid)
        indexed = {}
        for row in git(source, env, 'ls-files', '--stage', '-z').split(b'\0'):
            if row:
                metadata, path = row.split(b'\t', 1)
                mode, oid, stage = metadata.split()
                require(stage == b'0')
                indexed[path.decode()] = (mode, oid)
        require(indexed == expected)
        batch = git(source, env, 'cat-file', '--batch',
            content=b'\n'.join(oid for mode, oid in expected.values())+b'\n')
        offset = 0
        for name, (mode, oid) in expected.items():
            end = batch.index(b'\n', offset)
            header = batch[offset:end].split()
            require(len(header) == 3 and header[:2] == [oid, b'blob'])
            size, offset = int(header[2]), end+1
            path = checked_path(source/name)
            require(path.read_bytes() == batch[offset:offset+size])
            offset += size
            require(batch[offset:offset+1] == b'\n')
            offset += 1
        require(offset == len(batch))
        actual, directories = set(), set()
        for parent, names, files in os.walk(source/'src/pontius', followlinks=False):
            for name in names:
                path = checked_path(Path(parent)/name, True)
                directories.add(path.relative_to(source).as_posix())
            actual.update((Path(parent)/name).relative_to(source).as_posix() for name in files)
        require(actual == {path for path in expected if path.startswith('src/pontius/')})
        require(directories == {p.as_posix() for path in actual for p in Path(path).parents
                                if p.as_posix().startswith('src/pontius/')})
        for (path, count), digest in zip(SUITES.values(), TEST_HASHES):
            require(hashlib.sha256((source/path).read_bytes()).hexdigest() == digest)
        return BASE_TREE
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        raise HistoryRefusal('source_invalid') from error


def clone_history(source_root, target, env):
    checked_path(source_root, True)
    checked_path(target.parent, True, True)
    require(not target.exists(), 'input_invalid')
    require(git(source_root, env, 'rev-parse', BASE_COMMIT+'^{tree}').decode().strip() == BASE_TREE)
    git(source_root, env, '-c', 'core.hooksPath='+os.devnull, 'clone', '--no-hardlinks',
        '--no-checkout', str(source_root), str(target))
    git(target, env, 'config', 'core.autocrlf', 'false')
    git(target, env, '-c', 'core.hooksPath='+os.devnull, 'checkout', '--detach', BASE_COMMIT)
    checked_history(target, env)


def test_outcome(code, stderr, expected):
    match = re.search(rb'\bRan ([0-9]+) tests? in [0-9.]+s\r?\n\r?\n'
                      rb'(OK|FAILED)(?: \(([^\r\n]*)\))?\r?\n?\Z', stderr)
    count = int(match[1]) if match else 0
    skipped = re.search(rb'\bskipped=([0-9]+)\b', match[3] or b'') if match else None
    skips = int(skipped[1]) if skipped else 0
    passed = bool(match and match[2] == b'OK' and code == 0 and count == expected and skips == 0)
    return count, skips, passed


def write(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, sort_keys=True, indent=2)
        stream.write('\n')


def launch_suite(source, target, suite, env):
    path, expected = SUITES[suite]
    temp = target/'temp'/suite
    temp.mkdir()
    child_env = dict(env, TEMP=str(temp), TMP=str(temp))
    argv = [sys.executable, '-B', '-P', path]
    stdout, stderr = target/(suite+'-stdout.bin'), target/(suite+'-stderr.bin')
    write(target/(suite+'-intent.json'), dict(argv=argv, cwd=str(source), env=child_env))
    with stdout.open('xb') as out, stderr.open('xb') as err:
        process = subprocess.run(argv, cwd=source, env=child_env, stdout=out, stderr=err)
    count, skips, passed = test_outcome(process.returncode, stderr.read_bytes(), expected)
    result = dict(suite=suite, argv=argv, cwd=str(source), exit_code=process.returncode,
        tests=count, skips=skips, passed=passed, stdout=str(stdout), stderr=str(stderr))
    write(target/(suite+'-result.json'), result)
    return result


def run_history(source_root, run_root, suite):
    require(os.name == 'nt' and sys.implementation.name == 'cpython'
            and sys.version_info >= (3, 11) and sys.flags.safe_path and sys.dont_write_bytecode,
            'input_invalid')
    require(type(suite) is str and suite in (*SUITES, 'all'), 'input_invalid')
    native(Path(sys.executable))
    checked_path(source_root, True)
    checked_path(run_root.parent, True, True)
    require(run_root.is_absolute() and run_root.drive.upper() == 'D:'
            and '..' not in run_root.parts and not run_root.exists(), 'input_invalid')
    source, temp = run_root/'snapshot', run_root/'temp'
    env = environment(source, temp)
    require(git(source_root, env, 'rev-parse', BASE_COMMIT+'^{tree}').decode().strip() == BASE_TREE)
    run_root.mkdir()
    temp.mkdir()
    write(run_root/'intent.json', dict(commit=BASE_COMMIT, tree=BASE_TREE,
        python=str(native(Path(sys.executable))), git=env['PONTIUS_GIT'], suite=suite,
        source_root=str(source_root), version=sys.version))
    report = dict(commit=BASE_COMMIT, tree=BASE_TREE, complete=False, results=[], failure=None)
    try:
        clone_history(source_root, source, env)
        for selected in SUITES if suite == 'all' else (suite,):
            try:
                checked_history(source, env)
                report['results'].append(launch_suite(source, run_root, selected, env))
            except (OSError, ValueError, subprocess.SubprocessError) as error:
                report['results'].append(dict(suite=selected, passed=False, failure=type(error).__name__))
        checked_history(source, env)
        report['complete'] = all(row['passed'] for row in report['results'])
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        report['failure'] = type(error).__name__
    finally:
        write(run_root/'summary.json', report)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument('--source-root', type=Path, required=True)
    parser.add_argument('--run-root', type=Path, required=True)
    parser.add_argument('--suite', choices=(*SUITES, 'all'), required=True)
    args = parser.parse_args(argv)
    try:
        report = run_history(args.source_root, args.run_root, args.suite)
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        report = dict(complete=False, failure=type(error).__name__)
    print(json.dumps(report, sort_keys=True))
    return 0 if report['complete'] else 1


if __name__ == '__main__':
    sys.exit(main())
