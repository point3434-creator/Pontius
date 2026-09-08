"""Routine private coordination publication under workflow packet rule 6."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

root = Path('D:/Pontius-handoffs')
git_exe = 'C:/Program Files/Git/cmd/git.exe'
batch = sys.argv[1]
assert batch.isalnum()

def git(*args):
    return subprocess.run([git_exe, '--no-replace-objects', '-c',
        'safe.directory=' + root.as_posix(), '-C', str(root), *args],
        capture_output=True, check=True).stdout

assert git('branch', '--show-current').decode().strip() == 'main'
assert git('remote', 'get-url', 'origin').decode().strip() == (
    'https://github.com/point3434-creator/Pontius-handoffs.git')
assert not git('diff', '--cached', '--name-only').strip(), 'Unrelated staged work exists'
allowed = ('.gitattributes', 'INDEX.md', 'v0a-evaluation-opening/', 'v0a-evaluation-source/')
changed = git('diff', '--name-only').decode().splitlines()
assert all(path in allowed[:2] or path.startswith(allowed[2:]) for path in changed), changed
attributes = root / '.gitattributes'
rules = ('v0a-evaluation-opening/** -text', 'v0a-evaluation-source/** -text')
existing = attributes.read_text(encoding='utf-8')
missing = [rule for rule in rules if rule not in existing.splitlines()]
if missing:
    with attributes.open('a', encoding='utf-8', newline='\n') as stream:
        stream.write('\n# Preserve issued paired-evaluation packets and original receipt bytes.\n')
        stream.write('\n'.join(missing) + '\n')
git('-c', 'core.autocrlf=false', 'add', '--', '.gitattributes', 'INDEX.md',
    'v0a-evaluation-opening', 'v0a-evaluation-source')
staged = git('diff', '--cached', '--name-only').decode().splitlines()
assert staged and all(path in allowed[:2] or path.startswith(allowed[2:]) for path in staged)
for path in staged:
    assert git('show', ':' + path) == (root / path).read_bytes(), ('Raw staging drift', path)
git('-c', 'user.name=Codex', '-c', 'user.email=codex@localhost', 'commit', '-m',
    'Publish paired evaluation coordination ' + batch)
commit = git('rev-parse', 'HEAD').decode().strip()
git('push', 'origin', 'main')
remote = git('ls-remote', '--exit-code', 'origin', 'refs/heads/main').decode().split()[0]
assert remote == commit
assert not git('diff', '--cached', '--name-only').strip()
assert not git('diff', '--name-only', '--', *allowed[:2], *[p[:-1] for p in allowed[2:]]).strip()
output = Path('D:/Pontius/tmp/v0a-evaluation-source-r001') / ('handoff-publication-' + batch + '.json')
with output.open('x', encoding='utf-8', newline='\n') as stream:
    json.dump(dict(version='pontius-evaluation-handoff-publication-v1', commit=commit,
        remote_main=remote, paths=staged, repository=str(root),
        authority='docs/workflow.md handoff packet rule 6; coordination only'), stream, indent=2)
    stream.write('\n')
print(json.dumps(dict(commit=commit, remote_verified=True, files=len(staged), receipt=str(output))))
