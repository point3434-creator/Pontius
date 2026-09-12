"""Verify historical evidence and freeze before timing continuation."""
from pathlib import Path
from datetime import datetime, timezone
import subprocess
import ast
import sys
import experiment as e

here = Path(__file__).resolve().parent
assert not (here/'plan.json').exists()
for path in here.glob('*.py'):
    ast.parse(path.read_bytes())
    assert all(len(s) <= 100 and s == s.rstrip() for s in path.read_text().splitlines()), path
previous = {}
for directory in sorted(e.HISTORY.iterdir()):
    path = directory/'milestone-manifest.json'
    if path.is_file():
        for name, expected in e.read(path).items():
            assert e.digest(directory/name) == expected, (directory, name)
        previous[directory.name] = e.digest(path)
assert len(previous) == 25
assert previous[e.PRIOR.name] == (
    'e85b8f60865a11ef3e1e4749f234b8f4d36935a746eb122b0b052e9a15d4840f')
guard = e.HISTORY/'witness-guarded-repair-confirmation-001'/'verification-tools'
for label, cwd, tests in [('new', here, ['test_timing']),
    ('frozen', guard, ['test_gate', 'test_experiment'])]:
    result = subprocess.run([sys.executable, '-B', '-W', 'error::ResourceWarning',
        '-m', 'unittest', *tests, '-v'], cwd=cwd, capture_output=True, timeout=60)
    (here/(label+'-stdout.txt')).write_bytes(result.stdout)
    (here/(label+'-stderr.txt')).write_bytes(result.stderr)
    assert result.returncode == 0, result.stderr.decode()
for i in (0, 12, 32, 60):
    row, matrix, groups, coefficients = e.load_case(e.PRIOR/f'case-{i:03d}.json')
    record = e.c.train(matrix, groups, [10000])[0]
    assert record['coefficients'] == coefficients
    assert record['exact_exploitability'] == row['incumbent_score']['exact_exploitability']
e.c.equities_for.cache_clear()
e.write(here/'preflight.json', dict(passed=True, new_checks=5, frozen_checks=10,
    incumbent_replays=4, timed_candidates=0, prior_milestones=previous))
git = ['C:/Program Files/Git/cmd/git.exe', '-c', f'safe.directory={e.ROOT}', '-C', str(e.ROOT)]
head = subprocess.check_output(git+['rev-parse', 'HEAD'], text=True).strip()
names = subprocess.check_output(git+['diff', '--name-only'], text=True).splitlines()
e.write(here/'worktree-before.json', dict(head=head, modified_tracked_files={
    name: e.digest(e.ROOT/name) for name in names if (e.ROOT/name).is_file()}))
paths = {p.resolve() for p in here.iterdir() if p.is_file()}
paths.add(Path(sys.executable).resolve())
paths.add(e.c.MODEL)
sources = [str(e.PRIOR/f'case-{i:03d}.json') for i in range(64)]
paths.update(map(Path, sources))
paths.update(Path(e.read(p)['source_path']) for p in sources)
for name in previous:
    paths.add(e.HISTORY/name/'milestone-manifest.json')
old_pins = e.read(e.PRIOR/'plan.json')['pins']
for mod in tuple(sys.modules.values()):
    file = getattr(mod, '__file__', None)
    if file:
        file = Path(file).resolve()
        if file.suffix == '.py' and file.is_relative_to(e.ROOT):
            paths.add(file)
            if str(file) in old_pins:
                assert e.digest(file) == old_pins[str(file)], 'dependency drift'
output = Path('D:/Pontius-training/river-abstraction-study')/e.NAME
assert not output.exists()
plan = dict(name=e.NAME, output=str(output), sources=sources,
    pins={str(p): e.digest(p) for p in sorted(paths)}, source_head=head,
    budgets=[e.budgets(e.read(p)) for p in sources], block_updates=100, iteration_cap=200000,
    phase_timeout_seconds=900, python=sys.version, numpy=e.c.np.__version__,
    scipy=e.c.scipy.__version__, user_words_verbatim="Let's run it",
    fitting_tasks=0, fresh_boards=False, frozen_at_utc=datetime.now(timezone.utc).isoformat())
e.bindings(plan)
e.write(here/'plan.json', plan)
e.write(here/'freeze.json', dict(plan_sha256=e.digest(here/'plan.json'),
    cases=64, fresh_boards=False, pinned_files=len(plan['pins']),
    retained_invoked=False, new_lp_calls=0, timed_trajectories=64, gate_calls=128))
print(e.read(here/'freeze.json'))
