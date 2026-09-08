"""Commit/push the exact ADR-0511 candidate explicitly approved by the user."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess

main = Path('D:/Pontius')
work = main/'tmp/v0a-paired-closure-r001/authoring'
packet = Path('D:/Pontius-handoffs/v0a-paired-closure/r001')
git_exe = 'C:/Program Files/Git/cmd/git.exe'
base = 'dfd5a5c6a9d8aae6cbbae667f9b0716c59362eed'
candidate = 'e80b794050a466a3f8115b640b53dca3b51816a7'
tree = '16700b0b258288cf623e88a241abf264e8b08763'
origin = 'https://github.com/point3434-creator/Pontius.git'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def git(repo, *args):
    env = os.environ.copy()
    env['PONTIUS_GIT'] = git_exe
    env['PATH'] = str(Path(git_exe).parent)+os.pathsep+env.get('PATH', '')
    result = subprocess.run([git_exe, '--no-replace-objects', '-c',
        f'safe.directory={repo.as_posix()}', '-C', str(repo), *args],
        env=env, capture_output=True)
    if result.returncode:
        raise RuntimeError((args, result.returncode, result.stderr.decode(errors='replace')))
    return result.stdout


def tg(repo, *args):
    return git(repo, *args).decode().strip()


def remote():
    rows = tg(main, 'ls-remote', '--exit-code', 'origin', 'refs/heads/master').splitlines()
    assert len(rows) == 1
    commit, ref = rows[0].split()
    assert ref == 'refs/heads/master'
    return commit


def save(name, value):
    raw = (json.dumps(value, sort_keys=True, indent=2)+'\n').encode()
    with (packet/name).open('xb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())


identity = json.loads((packet/'candidate.json').read_bytes())
assert identity['commit'] == candidate and identity['tree'] == tree and identity['base'] == base
assert tg(work, 'rev-parse', identity['ref']) == candidate
assert tg(work, 'rev-parse', candidate+'^{tree}') == tree
assert tg(work, 'rev-parse', candidate+'^') == base
raw_summary = (packet/'acceptance-summary.json').read_bytes()
assert sha(raw_summary) == '947ac6d58ba249a7d2a4a9337872891c6650ae1d2a18fbee583ab0e57355f4ac'
summary = json.loads(raw_summary)
assert summary['candidate'] == identity and summary['metadata_test_executions'] == 24
for row in summary['reviews']:
    raw = (packet/row['path']).read_bytes()
    assert sha(raw) == row['sha256'] and b'Verdict: CLEAN' in raw
for row in summary['gates']:
    raw = (packet/row['receipt']).read_bytes()
    assert sha(raw) == row['sha256']
    assert all(r['exit_code'] == 0 and r['snapshot_head'] == candidate for r in json.loads(raw))
manifest = (packet/'manifest.sha256').read_bytes()
assert sha(manifest) == identity['manifest_sha256']
assert manifest.splitlines(keepends=True) == sorted(manifest.splitlines(keepends=True))
paths = []
for row in manifest.decode().splitlines():
    digest, path = row.split('  ', 1)
    raw = (packet/'files'/path).read_bytes()
    assert sha(raw) == digest and raw == git(work, 'cat-file', 'blob', candidate+':'+path)
    paths.append(path)
assert len(paths) == 5
assert sorted(paths) == sorted(tg(work, 'diff', '--no-renames', '--name-only', base, candidate).splitlines())
assert tg(main, 'rev-parse', 'HEAD') == base
assert tg(main, 'branch', '--show-current') == 'master'
assert not tg(main, 'status', '--porcelain', '--untracked-files=no')
assert tg(main, 'remote', 'get-url', 'origin') == origin
assert tg(main, 'remote', 'get-url', '--push', 'origin') == origin
assert remote() == base
existing = set(tg(main, 'ls-files').splitlines())
for path in paths:
    if path not in existing:
        assert not os.path.lexists(main/path)
assert not os.path.lexists(main/'tmp/v0a-paired-evaluation-run-001')
save('adoption-authorization.json', dict(user_message='lets do it',
    approval_question='Do you approve committing and pushing this exact ADR-0511 candidate, '
        'then running its single supervised 48-trial comparison?',
    candidate=identity, decision='ADR-0511', single_comparison_authorized=True,
    recorded_utc=datetime.now(timezone.utc).isoformat()))
for path in paths:
    target = main/path
    target.parent.mkdir(parents=True, exist_ok=True)
    raw = (packet/'files'/path).read_bytes()
    with target.open('wb' if path in existing else 'xb') as stream:
        stream.write(raw)
    assert target.read_bytes() == raw
git(main, '-c', 'core.autocrlf=false', 'add', '--', *paths)
assert tg(main, 'write-tree') == tree
git(main, 'diff', '--cached', '--check')
print(git(main, 'commit', '-m', 'Close the measured paired comparison contract').decode(), flush=True)
commit = tg(main, 'rev-parse', 'HEAD')
assert tg(main, 'rev-parse', 'HEAD^{tree}') == tree
assert tg(main, 'rev-parse', 'HEAD^') == base
remote_commit = remote()
if remote_commit != commit:
    assert remote_commit == base
    git(main, 'push', 'origin', 'HEAD:refs/heads/master')
assert remote() == commit
assert not tg(main, 'status', '--porcelain', '--untracked-files=no')
result = dict(status='COMMITTED_AND_PUSHED', commit=commit, tree=tree, parent=base,
    candidate=candidate, remote=origin, branch='master', remote_verified=True,
    recorded_utc=datetime.now(timezone.utc).isoformat(), comparison_started=False)
save('adoption-result.json', result)
print(json.dumps(result))
