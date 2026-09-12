"""Freeze the next board without constructing its payoff matrix or strategy."""
from pathlib import Path
from datetime import datetime, timezone
import ast
import subprocess
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
assert len(previous) == 26
assert previous[e.PRIOR.name] == (
    'b0156f8e25bf74514e0de54c1987b5e06b9b844abc2d3e69bab9fbb83f948238')
guard = e.HISTORY/'witness-guarded-repair-confirmation-001'/'verification-tools'
for label, cwd, tests in [('new', here, ['test_board']),
    ('timing', e.PRIOR/'verification-tools', ['test_timing']),
    ('frozen', guard, ['test_gate', 'test_experiment'])]:
    result = subprocess.run([sys.executable, '-B', '-W', 'error::ResourceWarning',
        '-m', 'unittest', *tests, '-v'], cwd=cwd, capture_output=True, timeout=60)
    (here/(label+'-stdout.txt')).write_bytes(result.stdout)
    (here/(label+'-stderr.txt')).write_bytes(result.stderr)
    assert result.returncode == 0, result.stderr.decode()
excluded, historical = e.c.historical_boards()
selection = e.select(excluded)
git = ['C:/Program Files/Git/cmd/git.exe', '-c', f'safe.directory={e.ROOT}', '-C', str(e.ROOT)]
head = subprocess.check_output(git+['rev-parse', 'HEAD'], text=True).strip()
names = subprocess.check_output(git+['diff', '--name-only'], text=True).splitlines()
e.write(here/'worktree-before.json', dict(head=head, modified_tracked_files={
    name: e.digest(e.ROOT/name) for name in names if (e.ROOT/name).is_file()}))
e.write(here/'preflight.json', dict(passed=True, tests=17, prior_milestones=previous,
    strategy_results_computed=0, historical_plans=len(historical)))
paths = {p.resolve() for p in here.iterdir() if p.is_file()}
paths.update(map(Path, historical))
paths.add(Path(sys.executable).resolve())
paths.add(e.c.MODEL)
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
plan = dict(name=e.NAME, output=str(output), selection=selection, excluded_boards=excluded,
    historical_plans=historical, entries=e.c.entries_for([selection['board']]),
    pins={str(p): e.digest(p) for p in sorted(paths)}, source_head=head,
    phase_timeout_seconds=900, python=sys.version, numpy=e.c.np.__version__,
    scipy=e.c.scipy.__version__, user_words_verbatim="Let's run the next board",
    fitting_tasks=0, fresh_boards=1, frozen_at_utc=datetime.now(timezone.utc).isoformat())
e.bindings(plan)
e.write(here/'plan.json', plan)
e.write(here/'freeze.json', dict(plan_sha256=e.digest(here/'plan.json'),
    cases=4, fresh_boards=1, selection=selection, pinned_files=len(plan['pins']),
    retained_invoked=False, lp_calls=16, gate_calls=16))
print(e.read(here/'freeze.json'))
