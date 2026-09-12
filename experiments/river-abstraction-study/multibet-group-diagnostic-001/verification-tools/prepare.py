"""Freeze a known-board action-menu diagnostic before research outcomes."""
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
assert len(previous) == 28
assert previous[e.PRIOR.name] == (
    'db3ebb182c52038b9e4ea3a3e0d9e18425e58242668e6650c0eb3d9bef304ee0')
test = subprocess.run([sys.executable, '-B', '-W', 'error::ResourceWarning',
    '-m', 'unittest', 'test_multi', '-v'], cwd=here, capture_output=True, timeout=60)
(here/'tests-stdout.txt').write_bytes(test.stdout)
(here/'tests-stderr.txt').write_bytes(test.stderr)
assert test.returncode == 0, test.stderr.decode()
assert {v['case']['texture'] for v in e.entries()} == set(e.c.TEXTURES)
git = ['C:/Program Files/Git/cmd/git.exe', '-c', f'safe.directory={e.ROOT}', '-C', str(e.ROOT)]
head = subprocess.check_output(git+['rev-parse', 'HEAD'], text=True).strip()
names = subprocess.check_output(git+['diff', '--name-only'], text=True).splitlines()
e.write(here/'worktree-before.json', dict(head=head, modified_tracked_files={
    name: e.digest(e.ROOT/name) for name in names if (e.ROOT/name).is_file()}))
e.write(here/'preflight.json', dict(passed=True, tests=5, prior_milestones=previous,
    research_outcomes_computed=0, fresh_boards=0))
paths = {p.resolve() for p in here.iterdir() if p.is_file()}
paths.add(e.INPUT/'plan.json')
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
plan = dict(name=e.NAME, output=str(output), entries=e.entries(), checkpoints=[10000, 50000],
    pins={str(p): e.digest(p) for p in sorted(paths)}, source_head=head,
    phase_timeout_seconds=900, python=sys.version, numpy=e.c.np.__version__,
    scipy=e.c.scipy.__version__, user_words_verbatim='interesting, lets test it out',
    fitting_tasks=0, fresh_boards=0, frozen_at_utc=datetime.now(timezone.utc).isoformat())
e.bindings(plan)
e.write(here/'plan.json', plan)
e.write(here/'freeze.json', dict(plan_sha256=e.digest(here/'plan.json'), cases=8,
    menus=3, lp_calls=144, trajectories=24, fitting_tasks=0, retained_invoked=False))
print(e.read(here/'freeze.json'))
