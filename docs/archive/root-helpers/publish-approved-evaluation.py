"""Publish only the two concrete actions explicitly approved with 'Commit and push'."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

p = argparse.ArgumentParser()
p.add_argument('action', choices=['verify', 'source', 'handoffs'])
a = p.parse_args()
git_exe = 'C:/Program Files/Git/cmd/git.exe'
main = Path('D:/Pontius')
work = main / 'tmp/v0a-evaluation-source-r001/authoring'
packet = main / 'tmp/v0a-evaluation-seal-r001/packets/r001'
source_packet = main / 'tmp/v0a-evaluation-source-r001/packets/r001'
home = Path('D:/Pontius-handoffs')
local = Path(__file__).parent
expected_candidate = '4f6096f274e4c8c8c05e4607651bf426d3b1ad9c'
expected_base = '34616938c708b1ca306b9d8a17b9d98e2f9e451f'
expected_tree = '54a257f4f2957696b9d33e7338ce140206a3f578'
main_origin = 'https://github.com/point3434-creator/Pontius.git'
handoff_origin = 'https://github.com/point3434-creator/Pontius-handoffs.git'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def git(repo, *args):
    env = os.environ.copy()
    env['PONTIUS_GIT'] = git_exe
    # Existing post-commit hooks use git by name: bind that lookup to native Git.
    env['PATH'] = str(Path(git_exe).parent) + os.pathsep + env.get('PATH', '')
    result = subprocess.run([git_exe, '--no-replace-objects', '-c',
        f'safe.directory={repo.as_posix()}', '-C', str(repo), *args],
        capture_output=True, env=env)
    if result.returncode:
        raise RuntimeError(f'Native Git failed ({result.returncode}): {args!r}\n'
                           + result.stderr.decode(errors='replace'))
    return result.stdout


def textgit(repo, *args):
    return git(repo, *args).decode().strip()


def remote(repo, branch):
    rows = textgit(repo, 'ls-remote', '--exit-code', 'origin', 'refs/heads/' + branch).splitlines()
    assert len(rows) == 1
    commit, ref = rows[0].split()
    assert ref == 'refs/heads/' + branch and re.fullmatch('[0-9a-f]{40}', commit)
    return commit


def save(name, value):
    value['recorded_utc'] = datetime.now(timezone.utc).isoformat()
    raw = (json.dumps(value, sort_keys=True, indent=2) + '\n').encode()
    with (packet / name).open('xb') as stream:
        assert stream.write(raw) == len(raw)
        stream.flush()
        os.fsync(stream.fileno())


def bound_json(path, expected):
    raw = path.read_bytes()
    assert sha(raw) == expected, path
    return json.loads(raw)


def verify_source():
    identity = json.loads((packet / 'candidate.json').read_bytes())
    assert identity['commit'] == expected_candidate and identity['tree'] == expected_tree
    assert identity['base'] == expected_base
    assert identity['manifest_sha256'] == '983ed0dbf779f7fa96755ef4d87081506d0293cebcc8273aa187c6a3126dcc47'
    assert textgit(work, 'rev-parse', identity['ref']) == expected_candidate
    assert textgit(work, 'rev-parse', expected_candidate + '^') == expected_base
    assert textgit(work, 'rev-parse', expected_candidate + '^{tree}') == expected_tree
    manifest = (packet / 'manifest.sha256').read_bytes()
    assert sha(manifest) == identity['manifest_sha256']
    assert manifest.decode().splitlines(keepends=True) == sorted(manifest.decode().splitlines(keepends=True))
    paths = []
    for row in manifest.decode().splitlines():
        digest, path = row.split('  ', 1)
        assert not Path(path).is_absolute() and '..' not in Path(path).parts
        raw = (packet / 'files' / path).read_bytes()
        assert sha(raw) == digest and raw == git(work, 'cat-file', 'blob', expected_candidate + ':' + path)
        paths.append(path)
    assert len(paths) == len(set(paths)) == 14
    assert sorted(paths) == sorted(textgit(work, 'diff', '--name-only', expected_base, expected_candidate).splitlines())
    source = bound_json(source_packet / 'checks/final-acceptance-summary.json',
        'de8544829b01d05d5f2ff2d3b3b5168bdff20b8de40355368aeb000af03e9bcb')
    meta = bound_json(packet / 'checks/metadata-acceptance-summary.json',
        '786031fd88528112902d54e098b2aabafc924e52d574ee1c5baa78af97b0050d')
    assert source['candidate']['commit'] == 'bca326c6bfedd71324a19c809f617e267cc9e0a2'
    assert meta['candidate'] == identity and meta['tests'] == 24 and meta['commands'] == 4
    assert all(v['commands'] == 16 and v['tests'] == 296 and v['skips'] == 0
               for v in source['totals'].values())
    for summary, field, candidate in ((source, 'acceptance_receipts', source['candidate']['commit']),
                                       (meta, 'receipts', expected_candidate)):
        for row in summary[field]:
            records = bound_json(Path(row['receipt']), row['sha256'])
            assert len(records) == 2 and all(r['exit_code'] == 0 and r['snapshot_head'] == candidate for r in records)
    for path, digest in (
        (source_packet / 'reviews/review-a.md', '034bc3a780b0e83c34519707183dff5dc33fedab6289efa4a0407f554b4e09cc'),
        (source_packet / 'reviews/review-b.md', '255af51e120b379e371083724f011c5edc314a577a1b4a3655ed7b34d4786346'),
        (packet / 'reviews/review-light.md', '5450a674f148419f160e071d738a812f275015cba0381af42f142c25f7de5ee7'),
    ):
        assert sha(path.read_bytes()) == digest
    assert not textgit(main, 'status', '--porcelain', '--untracked-files=no')
    assert textgit(main, 'branch', '--show-current') == 'master'
    assert textgit(main, 'rev-parse', 'HEAD') == expected_base
    assert textgit(main, 'remote', 'get-url', '--push', 'origin') == main_origin
    assert textgit(main, 'remote', 'get-url', 'origin') == main_origin
    existing = set(textgit(main, 'ls-files').splitlines())
    for path in paths:
        target = main / path
        if path not in existing:
            assert not target.exists(), ('new-path collision', path)
        else:
            assert target.is_file() and not target.is_symlink()
    assert remote(main, 'master') == expected_base, 'Remote primary advanced'
    return identity, paths, existing


def verify_handoffs():
    proposal = bound_json(local / 'evaluation-handoff-upload-manifest.json',
        'ebcf0d53925fb6a3d1aa876f322125240f26448bdf5f5fc5280dc6385c42e1bf')
    assert proposal['destination'] == handoff_origin and proposal['branch'] == 'main'
    assert proposal['file_count'] == len(proposal['files']) == 258
    assert proposal['total_bytes'] == 20332596
    raw_attributes = (local / 'evaluation-handoff-proposed.gitattributes').read_bytes()
    for row in proposal['files']:
        path = row['path']
        assert path in ('.gitattributes', 'INDEX.md') or path.split('/')[0] in (
            'v0a-evaluation-opening', 'v0a-evaluation-source', 'v0a-evaluation-seal')
        assert '..' not in Path(path).parts and not Path(path).is_absolute()
        if path == '.gitattributes':
            assert sha((home / path).read_bytes()) == row['original_sha256']
            raw = raw_attributes
        else:
            raw = (home / path).read_bytes()
        assert len(raw) == row['bytes'] and sha(raw) == row['sha256'], path
    assert not textgit(home, 'diff', '--cached', '--name-only'), 'Handoff index already occupied'
    assert textgit(home, 'diff', '--name-only').splitlines() == ['INDEX.md']
    assert textgit(home, 'branch', '--show-current') == 'main'
    assert textgit(home, 'remote', 'get-url', '--push', 'origin') == handoff_origin
    assert textgit(home, 'remote', 'get-url', 'origin') == handoff_origin
    head = textgit(home, 'rev-parse', 'HEAD')
    assert head == 'cb8cb9962001cd6d70da444c643faf54c42c1b16'
    assert remote(home, 'main') == head, 'Handoff remote advanced'
    return proposal, raw_attributes, head


if a.action == 'verify':
    identity, paths, existing = verify_source()
    proposal, _, head = verify_handoffs()
    print(json.dumps(dict(status='VERIFIED', source_candidate=identity['commit'], source_paths=len(paths),
        source_base=expected_base, handoff_files=proposal['file_count'], handoff_bytes=proposal['total_bytes'],
        handoff_base=head, remote_destinations_verified=True, tests_rerun=False)))
elif a.action == 'source':
    assert not (packet / 'authorization.json').exists() and not (packet / 'commit-result.json').exists()
    identity, paths, existing = verify_source()
    save('authorization.json', dict(user_message='Commit and push', decision='ADR-0509',
        title='Source-seal the paired local evaluation loop', approved_candidate=identity,
        actions=['incorporate exact fourteen reviewed blobs', 'commit and push origin/master'],
        actual_evaluation_authorized=False))
    for path in paths:
        target = main / path
        target.parent.mkdir(parents=True, exist_ok=True)
        raw = (packet / 'files' / path).read_bytes()
        if path in existing:
            target.write_bytes(raw)
        else:
            with target.open('xb') as stream:
                assert stream.write(raw) == len(raw)
        assert target.read_bytes() == raw
    git(main, '-c', 'core.autocrlf=false', 'add', '--', *paths)
    assert textgit(main, 'write-tree') == expected_tree
    git(main, 'diff', '--cached', '--check')
    print(git(main, 'commit', '-m', 'Source-seal the paired local evaluation loop').decode(), flush=True)
    commit = textgit(main, 'rev-parse', 'HEAD')
    assert textgit(main, 'rev-parse', 'HEAD^{tree}') == expected_tree
    assert textgit(main, 'rev-parse', 'HEAD^') == expected_base
    remote_commit = remote(main, 'master')
    hook_pushed = remote_commit == commit
    if not hook_pushed:
        assert remote_commit == expected_base
        git(main, 'push', 'origin', 'HEAD:refs/heads/master')
    assert remote(main, 'master') == commit
    assert not textgit(main, 'status', '--porcelain', '--untracked-files=no')
    result = dict(status='COMMITTED_AND_PUSHED', commit=commit, tree=expected_tree, parent=expected_base,
        approved_candidate=identity['commit'], manifest_sha256=identity['manifest_sha256'],
        remote=main_origin, branch='master', remote_verified=True, tracked_and_index_clean=True,
        post_commit_hook_push_verified=hook_pushed, source_seal_adopted=True, actual_evaluation_executed=False)
    save('commit-result.json', result)
    print(json.dumps(result))
else:
    assert not (packet / 'handoff-publication-result.json').exists()
    proposal, raw_attributes, head = verify_handoffs()
    assert json.loads((packet / 'commit-result.json').read_bytes())['status'] == 'COMMITTED_AND_PUSHED'
    save('handoff-publication-authorization.json', dict(user_message='Yes',
        approval_question='Do you explicitly approve uploading the 258-file, approximately 20.3 MB '
            'coordination packet, containing source copies, review reports and test receipts, '
            'to Pontius-handoffs?',
        approved_upload_manifest_sha256='ebcf0d53925fb6a3d1aa876f322125240f26448bdf5f5fc5280dc6385c42e1bf',
        destination=handoff_origin, branch='main', files=258, bytes=20332596,
        prior_automatic_rejection='User now explicitly approved the separate upload question'))
    (home / '.gitattributes').write_bytes(raw_attributes)
    paths = [r['path'] for r in proposal['files']]
    git(home, '-c', 'core.autocrlf=false', 'add', '--', *paths)
    assert sorted(textgit(home, 'diff', '--cached', '--name-only').splitlines()) == sorted(paths)
    for row in proposal['files']:
        assert sha(git(home, 'show', ':' + row['path'])) == row['sha256'], row['path']
    tree = textgit(home, 'write-tree')
    print(git(home, 'commit', '-m', 'Publish paired evaluation source and seal acceptance packets').decode(), flush=True)
    commit = textgit(home, 'rev-parse', 'HEAD')
    assert textgit(home, 'rev-parse', 'HEAD^') == head
    assert textgit(home, 'rev-parse', 'HEAD^{tree}') == tree
    remote_commit = remote(home, 'main')
    hook_pushed = remote_commit == commit
    if not hook_pushed:
        assert remote_commit == head
        git(home, 'push', 'origin', 'HEAD:refs/heads/main')
    assert remote(home, 'main') == commit
    assert not textgit(home, 'status', '--porcelain', '--untracked-files=no')
    result = dict(status='COMMITTED_AND_PUSHED', commit=commit, tree=tree, parent=head,
        remote=handoff_origin, branch='main', remote_verified=True, files=258, bytes=20332596,
        upload_manifest_sha256='ebcf0d53925fb6a3d1aa876f322125240f26448bdf5f5fc5280dc6385c42e1bf',
        tracked_and_index_clean=True, post_commit_hook_push_verified=hook_pushed)
    save('handoff-publication-result.json', result)
    print(json.dumps(result))
