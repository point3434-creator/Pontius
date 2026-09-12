"""Freeze byte identities and run checks before the first captured research state."""
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
result = subprocess.run([sys.executable, '-B', '-W', 'error::ResourceWarning',
    '-m', 'unittest', 'test_kernel', 'test_inputs', '-v'], cwd=here,
    capture_output=True, timeout=60)
(here/'tests-stdout.txt').write_bytes(result.stdout)
(here/'tests-stderr.txt').write_bytes(result.stderr)
assert result.returncode == 0, result.stderr.decode()
assert e.read(here/'capacity.json')['passed']
previous = {}
for directory in sorted(e.HISTORY.iterdir()):
    path = directory/'milestone-manifest.json'
    if path.is_file():
        for name, expected in e.read(path).items():
            assert e.digest(directory/name) == expected, (directory, name)
        previous[directory.name] = e.digest(path)
assert len(previous) == 32, len(previous)
baseline_doc = e.ROOT/'docs/research/river-multibet-size-repair-baseline.md'
assert e.digest(baseline_doc) == '924b7fb3f05f5f19f2ace062af4d3b9704854ddc5686e756b5e0d90bc2238a2d'
git = ['C:/Program Files/Git/cmd/git.exe', '-c', f'safe.directory={e.ROOT}', '-C', str(e.ROOT)]
head = subprocess.check_output(git+['rev-parse', 'HEAD'], text=True).strip()
names = subprocess.check_output(git+['diff', '--name-only'], text=True).splitlines()
e.write(here/'worktree-before.json', dict(head=head, modified_tracked_files={
    name: e.digest(e.ROOT/name) for name in names if (e.ROOT/name).is_file()}))
e.write(here/'preflight.json', dict(passed=True, tests=8, prior_milestones=previous,
                                  captured_states=0, research_outcomes=0))
paths = {p.resolve() for p in here.iterdir() if p.is_file()}
paths.update(p.resolve() for p in e.BASELINE.rglob('*') if p.is_file())
paths.update(e.HISTORY/name/'milestone-manifest.json' for name in previous)
paths.update([Path(sys.executable).resolve(), e.c.MODEL, baseline_doc])
paths.add(e.EXTERNAL/'pluribus_lite/evaluator.py')
for mod in tuple(sys.modules.values()):
    file = getattr(mod, '__file__', None)
    if file:
        p = Path(file).resolve()
        if p.is_file() and (p.is_relative_to(e.ROOT) or p.is_relative_to(e.EXTERNAL)):
            paths.add(p)
output = Path('D:/Pontius-training/river-abstraction-study')/e.NAME
assert not output.exists()
plan = dict(name=e.NAME, output=str(output), source_head=head,
    pins={str(p): e.digest(p) for p in sorted(paths)},
    python=sys.version, numpy=e.np.__version__, scipy=e.c.scipy.__version__,
    evaluator=e.evaluator.BACKEND, capture=dict(seed=e.inputs.SEED, target=4, max_hands=2000),
    phase_timeout_seconds=1800, fitting_tasks=0,
    user_words_verbatim="Let's move forward with next research",
    frozen_at_utc=datetime.now(timezone.utc).isoformat())
e.bindings(plan)
e.write(here/'plan.json', plan)
e.write(here/'freeze.json', dict(plan_sha256=e.digest(here/'plan.json'), cases=4,
    lp_calls=24, retained_invoked=False, previous_milestones=len(previous)))
print(e.read(here/'freeze.json'))
