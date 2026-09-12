"""Read-only final verification of the named milestone and unchanged source state."""
from pathlib import Path
from hashlib import sha256
import json
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = Path('D:/Pontius-worktrees/eval-runner-consolidation')
HISTORY = ROOT/'experiments/river-abstraction-study'
ARCHIVE = HISTORY/'witness-compute-matched-continuation-001'
read = lambda p: json.loads(p.read_bytes())
digest = lambda p: sha256(p.read_bytes()).hexdigest()
retained = read(HERE/'retention.json')
assert retained['passed'] and not retained['commit'] and not retained['push']
assert digest(ARCHIVE/'milestone-manifest.json') == retained['milestone_sha256']
count, members = 0, 0
for directory in HISTORY.iterdir():
    manifest = directory/'milestone-manifest.json'
    if manifest.is_file():
        items = read(manifest)
        for name, expected in items.items():
            assert digest(directory/name) == expected, (directory, name)
        count += 1
        members += len(items)
assert count == 26
items = read(ARCHIVE/'milestone-manifest.json')
assert len(items) == retained['members']
assert set(items) == {p.relative_to(ARCHIVE).as_posix() for p in ARCHIVE.rglob('*')
                      if p.is_file() and p != ARCHIVE/'milestone-manifest.json'}
plan = read(ARCHIVE/'plan.json')
for path, expected in plan['pins'].items():
    assert digest(Path(path)) == expected, path
report = ROOT/'docs/research/river-witness-compute-matched-continuation-001.md'
assert digest(report) == digest(ARCHIVE/'report.md') == retained['report_sha256']
assert (ROOT/'docs/research/README.md').read_bytes().startswith(
    (HERE/'research-readme-before.md').read_bytes())
before = read(HERE/'worktree-before.json')
for name, expected in before['modified_tracked_files'].items():
    if name != 'docs/research/README.md':
        assert digest(ROOT/name) == expected, name
git = ['C:/Program Files/Git/cmd/git.exe', '-c', f'safe.directory={ROOT}', '-C', str(ROOT)]
assert subprocess.check_output(git+['rev-parse', 'HEAD'], text=True).strip() == before['head']
print(json.dumps(dict(passed=True, milestones=count, verified_members=members,
    current_members=len(items), pins=len(plan['pins']), source_head=before['head'])))
