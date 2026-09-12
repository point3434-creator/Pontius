"""Freeze a bounded plan only after preflight, before research outcomes."""
from pathlib import Path
from datetime import datetime, timezone
import ast
import subprocess
import sys
import experiment as e
from variants import Trainer
from test_variants import Updates

here = Path(__file__).resolve().parent
assert not (here/'plan.json').exists()
for p in here.glob('*.py'):
    ast.parse(p.read_bytes())
result = subprocess.run([sys.executable, '-B', '-W', 'error::ResourceWarning',
    '-m', 'unittest', 'test_variants', 'test_analysis', '-v'], cwd=here,
    capture_output=True, timeout=60)
(here/'tests-stdout.txt').write_bytes(result.stdout)
(here/'tests-stderr.txt').write_bytes(result.stderr)
assert result.returncode == 0, result.stderr.decode()
for mode in e.MODES:
    a = Trainer(Updates.game(), [[0, 1], [0, 1]], mode)
    b = e.Reference(Updates.game(), [[0, 1], [0, 1]], mode)
    for _ in range(500):
        a.step()
        b.step()
    assert a.average() == b.average()
previous = {}
for directory in sorted(e.HISTORY.iterdir()):
    manifest = directory/'milestone-manifest.json'
    if manifest.exists():
        for name, expected in e.read(manifest).items():
            assert e.digest(directory/name) == expected, (directory, name)
        previous[directory.name] = e.digest(manifest)
assert previous[e.PRIOR.name] == (
    '3ec8544fa91ccc4566675086689e12359f4f4194a9461bcf6684cc7c9e52bda9')
git = ['C:/Program Files/Git/cmd/git.exe', '-c', f'safe.directory={e.ROOT}', '-C', str(e.ROOT)]
head = subprocess.check_output(git+['rev-parse', 'HEAD'], text=True).strip()
names = subprocess.check_output(git+['diff', '--name-only'], text=True).splitlines()
e.write(here/'worktree-before.json', dict(head=head, modified_tracked_files={
    name: e.digest(e.ROOT/name) for name in names if (e.ROOT/name).is_file()}))
e.write(here/'preflight.json', dict(passed=True, analytic_checks=8,
    independent_replay_small_games=3, prior_milestones=previous, outcomes_computed=0))
sources = [e.PRIOR/'baseline'/f'case-{i:03d}.json' for i in range(16)]
paths = {p.resolve() for p in here.iterdir() if p.is_file()}
paths.update(sources)
paths.add(Path(sys.executable).resolve())
paths.add(e.c.MODEL)
for mod in tuple(sys.modules.values()):
    path = getattr(mod, '__file__', None)
    if path:
        p = Path(path).resolve()
        if p.suffix == '.py' and p.is_relative_to(e.ROOT):
            paths.add(p)
for name in previous:
    paths.add(e.HISTORY/name/'milestone-manifest.json')
output = Path('D:/Pontius-training/river-abstraction-study')/e.NAME
assert not output.exists()
plan = dict(name=e.NAME, output=str(output), sources=list(map(str, sources)),
    checkpoints=e.CHECKPOINTS, modes=list(e.MODES), repetitions=2,
    pins={str(p): e.digest(p) for p in sorted(paths)}, source_head=head,
    python=sys.version, numpy=e.m.np.__version__, scipy=e.c.scipy.__version__,
    phase_timeout_seconds=900, user_words_verbatim=
    "Thanks for looking. Let's move on to the next research then.",
    frozen_at_utc=datetime.now(timezone.utc).isoformat(), new_lp_calls=0,
    primary_residual_target='0.001', secondary_residual_target='0.0001',
    averaging=dict(rm='uniform', rm_plus='t^2', discounted='t^2'),
    discount_parameters=[1.5, 0, 2], fresh_board_confirmation=False)
e.bindings(plan)
e.write(here/'plan.json', plan)
e.write(here/'freeze.json', dict(plan_sha256=e.digest(here/'plan.json'), cases=16,
    variants=3, repetitions=2, preflight_passed=True, retained_invoked=False))
print(e.read(here/'freeze.json'))
