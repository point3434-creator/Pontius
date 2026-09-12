"""Freeze new adapter and all retained dependencies before computing outcomes."""
import experiment as e
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone

HERE = Path(__file__).resolve().parent
assert not (HERE/'plan.json').exists()
check = subprocess.run([sys.executable, '-B', '-W', 'error::ResourceWarning',
    '-m', 'unittest', 'test_stack', '-v'], cwd=HERE, capture_output=True, timeout=60)
(HERE/'tests-stdout.txt').write_bytes(check.stdout)
(HERE/'tests-stderr.txt').write_bytes(check.stderr)
assert check.returncode == 0, check.stderr.decode()
previous = {}
for directory in sorted(e.HISTORY.iterdir()):
    manifest = directory/'milestone-manifest.json'
    if manifest.is_file():
        for member, value in e.read(manifest).items():
            assert e.digest(directory/member) == value
        previous[directory.name] = e.digest(manifest)
assert len(previous) == 33
assert previous[e.PRIOR.name] == '318c9d561b2b1d62ffe988c873e24b2f135914b24935fe13d786af7b2e063007'
git = ['C:/Program Files/Git/cmd/git.exe', '-c', f'safe.directory={e.ROOT}', '-C', str(e.ROOT)]
head = subprocess.check_output(git+['rev-parse', 'HEAD'], text=True).strip()
names = subprocess.check_output(git+['diff', '--name-only'], text=True).splitlines()
e.write(HERE/'worktree-before.json', dict(head=head, modified_tracked_files={
    name: e.digest(e.ROOT/name) for name in names if (e.ROOT/name).is_file()}))
e.write(HERE/'preflight.json', dict(passed=True, tests=4, prior_milestones=previous,
                                  actual_payoff_solver_outcomes=0))
paths = {p.resolve() for p in HERE.iterdir() if p.is_file()}
paths.update(p.resolve() for p in e.PRIOR.rglob('*') if p.is_file())
paths.update(e.HISTORY/name/'milestone-manifest.json' for name in previous)
old = e.read(e.PRIOR/'plan.json')['pins']
for path, expected in old.items():
    assert e.digest(path) == expected, path
    paths.add(Path(path))
output = Path('D:/Pontius-training/river-abstraction-study')/e.NAME
assert not output.exists()
plan = dict(name=e.NAME, output=str(output), cases=list(range(4)), expected_applicable=[1],
    source_head=head, python=sys.version, numpy=e.b.np.__version__,
    scipy=e.b.c.scipy.__version__, evaluator=e.b.e.evaluator.BACKEND,
    phase_timeout_seconds=1800, user_words_verbatim='lets move on',
    pins={str(p): e.digest(p) for p in sorted(paths)},
    frozen_at_utc=datetime.now(timezone.utc).isoformat())
e.bindings(plan)
e.write(HERE/'plan.json', plan)
e.write(HERE/'freeze.json', dict(plan_sha256=e.digest(HERE/'plan.json'),
    prior_milestones=len(previous), retained_invoked=False))
print(e.read(HERE/'freeze.json'))
