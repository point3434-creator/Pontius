"""Freeze deterministic board selection and dependencies before new-board scoring."""
from datetime import datetime, timezone
import ast
from pathlib import Path
import subprocess
import sys
import confirmation as c

here = Path(__file__).resolve().parent
assert not (here/'plan.json').exists(), 'freeze already exists'
for path in here.glob('*.py'):
    ast.parse(path.read_bytes())
    assert all(len(line) <= 100 and line == line.rstrip()
               for line in path.read_text().splitlines()), path

previous = {}
for directory in sorted(c.HISTORY.iterdir()):
    path = directory/'milestone-manifest.json'
    if path.is_file():
        for name, expected in c.read(path).items():
            assert c.digest(directory/name) == expected, (directory, name)
        previous[directory.name] = c.digest(path)
assert len(previous) == 21
assert previous['witness-group-repair-001'] == (
    'acdd5a2eaa54b31180cb692450e466cce4ae8a52a25e78dab62a0e760ec84f0a')

checks = []
for label, cwd, tests in [('admission', here, ['test_confirmation']),
    ('frozen-kernels', c.PREVIOUS/'verification-tools', ['test_repair', 'test_runner'])]:
    result = subprocess.run([sys.executable, '-B', '-W', 'error::ResourceWarning',
        '-m', 'unittest', *tests, '-v'], cwd=cwd, capture_output=True, timeout=60)
    (here/(label+'-stdout.txt')).write_bytes(result.stdout)
    (here/(label+'-stderr.txt')).write_bytes(result.stderr)
    assert result.returncode == 0, (label, result.stderr.decode())
    checks.append(dict(suite=label, exit=result.returncode))

# Reproduce already-observed pilot inputs: both regimes and both bets, one board.
old_plan = c.read(c.PREVIOUS/'plan.json')
for i in range(4):
    old = c.read(c.PREVIOUS/f'case-{i:03d}.json')
    matrix, groups, inputs = c.build_case(old['entry'])
    original = c.read(Path(old['entry']['original']))
    assert groups == old['baseline_groups'], 'ordinary-preference groups changed'
    assert inputs['joint'] == original['inputs']['joint']
    assert inputs['hands'] == original['inputs']['hands']
    assert inputs['ranges'] == original['inputs']['ranges']
    assert inputs['provenance_digest'] == original['provenance_digest']
c.equities_for.cache_clear()
c.write(here/'preflight.json', dict(passed=True, new_tests=6, frozen_tests=10,
    prior_cells_reconstructed=4, fresh_board_games_evaluated=0, suites=checks,
    prior_milestones_verified=previous))

git = ['C:/Program Files/Git/cmd/git.exe', '-c', f'safe.directory={c.ROOT}', '-C', str(c.ROOT)]
head = subprocess.check_output(git+['rev-parse', 'HEAD'], text=True).strip()
names = subprocess.check_output(git+['diff', '--name-only'], text=True).splitlines()
c.write(here/'worktree-before.json', dict(head=head, modified_tracked_files={
    name: c.digest(c.ROOT/name) for name in names if (c.ROOT/name).is_file()}))
excluded, historical_pins = c.historical_boards()
boards, receipt = c.select_boards(excluded)
paths = {p.resolve() for p in here.iterdir() if p.is_file()}
paths.add(Path(sys.executable).resolve())
paths.add(c.MODEL)
for directory in previous:
    paths.add(c.HISTORY/directory/'milestone-manifest.json')
for mod in tuple(sys.modules.values()):
    file = getattr(mod, '__file__', None)
    if file:
        file = Path(file).resolve()
        if file.suffix == '.py' and file.is_relative_to(c.ROOT):
            paths.add(file)
            if str(file) in old_plan['pins']:
                assert c.digest(file) == old_plan['pins'][str(file)], 'source drift'
pins = {str(p): c.digest(p) for p in sorted(paths)}
pins.update(historical_pins)
output = Path('D:/Pontius-training/river-abstraction-study')/c.NAME
assert not output.exists()
plan = dict(schema=c.NAME, milestone=c.NAME, boards=boards, excluded_boards=excluded,
    selection_receipt=receipt, selection_seed=c.SEED, entries=c.entries_for(boards),
    historical_plans=historical_pins, pins=pins, output=str(output),
    control_checkpoints=[10000, 50000], repaired_checkpoints=[1000, 10000],
    phase_timeout_seconds=900, fitting_tasks=0, python=sys.version,
    numpy=c.np.__version__, scipy=c.scipy.__version__, source_head=head,
    user_words_verbatim='lets confirm run on fresh boards',
    frozen_at_utc=datetime.now(timezone.utc).isoformat())
# JSON normalization of canonical-board tuples before checking the bound plan.
plan = c.json.loads(c.json.dumps(plan))
c.bindings(plan)
c.write(here/'plan.json', plan)
c.write(here/'freeze.json', dict(plan_sha256=c.digest(here/'plan.json'),
    pinned_files=len(pins), excluded_board_classes=len(excluded), boards=16, cases=64,
    lp_calls=256, trajectories=128, fitting_tasks=0, retained_invoked=False,
    phase_timeout_seconds=900, hard_rss_cap=None))
print(c.read(here/'freeze.json'))
