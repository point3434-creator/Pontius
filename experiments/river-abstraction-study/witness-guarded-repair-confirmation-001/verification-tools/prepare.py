"""Preflight and freeze before evaluating any new-board game."""
from pathlib import Path
from datetime import datetime, timezone
import sys
import ast
import subprocess
import json
import experiment as e
import gate

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
assert len(previous) == 23
assert previous['witness-repair-regression-diagnostic-001'] == (
    '12d9a49f57b6e0a34e53a0289488341038a5dfcd8efd00d2fcfe8f36e27c4f58')
for label, cwd, tests in [('new', here, ['test_gate', 'test_experiment']),
    ('frozen', e.c.PREVIOUS/'verification-tools', ['test_repair', 'test_runner'])]:
    result = subprocess.run([sys.executable, '-B', '-W', 'error::ResourceWarning',
        '-m', 'unittest', *tests, '-v'], cwd=cwd, capture_output=True, timeout=60)
    (here/(label+'-stdout.txt')).write_bytes(result.stdout)
    (here/(label+'-stderr.txt')).write_bytes(result.stderr)
    assert result.returncode == 0, result.stderr.decode()
for i in (0, 12, 32, 60):
    row = e.read(e.PRIOR/f'case-{i:03d}.json')
    matrix, groups, inputs = e.c.build_case(row['entry'])
    assert groups == row['baseline_groups'] and inputs == row['inputs']
    chosen = gate.select(matrix, groups, row['records']['control'][0]['coefficients'],
        row['proposal']['groups'], row['records']['repaired'][1]['coefficients'])
    score = e.c.score(matrix, chosen['groups'], chosen['coefficients'])
    known = e.read(e.HISTORY/'witness-repair-regression-diagnostic-001'/f'case-{i+32:03d}.json')
    assert score['exact_exploitability'] == known['gates']['security']['actual_exact']
e.c.equities_for.cache_clear()
e.write(here/'preflight.json', dict(passed=True, new_tests=10, frozen_tests=10,
    historical_cases_reproduced=4, new_boards_evaluated=0, prior_milestones=previous))
git = ['C:/Program Files/Git/cmd/git.exe', '-c', f'safe.directory={e.ROOT}', '-C', str(e.ROOT)]
head = subprocess.check_output(git+['rev-parse', 'HEAD'], text=True).strip()
names = subprocess.check_output(git+['diff', '--name-only'], text=True).splitlines()
e.write(here/'worktree-before.json', dict(head=head, modified_tracked_files={
    name: e.digest(e.ROOT/name) for name in names if (e.ROOT/name).is_file()}))
excluded, history_pins = e.c.historical_boards()
boards, receipt = e.select_boards(excluded)
paths = {p.resolve() for p in here.iterdir() if p.is_file()}
paths.add(Path(sys.executable).resolve())
paths.add(e.c.MODEL)
for name in previous:
    paths.add(e.HISTORY/name/'milestone-manifest.json')
for module in tuple(sys.modules.values()):
    file = getattr(module, '__file__', None)
    if file:
        file = Path(file).resolve()
        if file.suffix == '.py' and file.is_relative_to(e.ROOT):
            paths.add(file)
pins = {str(p): e.digest(p) for p in sorted(paths)}
pins.update(history_pins)
output = Path('D:/Pontius-training/river-abstraction-study')/e.NAME
assert not output.exists()
plan = dict(name=e.NAME, output=str(output), pins=pins, historical_plans=history_pins,
    boards=boards, excluded_boards=excluded, selection_receipt=receipt, selection_seed=e.NAME,
    entries=e.c.entries_for(boards), control_checkpoints=[10000, 50000],
    repaired_checkpoints=[1000, 10000], phase_timeout_seconds=900,
    source_head=head, python=sys.version, numpy=e.c.np.__version__, scipy=e.c.scipy.__version__,
    user_words_verbatim="Let's build and run it", fitting_tasks=0,
    frozen_at_utc=datetime.now(timezone.utc).isoformat())
plan = json.loads(json.dumps(plan))
e.bindings(plan)
e.write(here/'plan.json', plan)
e.write(here/'freeze.json', dict(plan_sha256=e.digest(here/'plan.json'),
    boards=16, cases=64, excluded_board_classes=len(excluded), pinned_files=len(pins),
    retained_invoked=False, lp_calls=256, solver_trajectories=128, gate_calls=64))
print(e.read(here/'freeze.json'))
