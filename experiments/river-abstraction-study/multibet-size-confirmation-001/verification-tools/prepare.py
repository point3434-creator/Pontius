"""Freeze unseen-board selection and all executable dependencies before evaluation."""
from pathlib import Path
from datetime import datetime, timezone
from itertools import permutations
from collections import Counter
import ast
import difflib
import subprocess
import sys
import experiment as e

here = Path(__file__).resolve().parent
assert not (here/'plan.json').exists()
for path in here.glob('*.py'):
    ast.parse(path.read_bytes())
    if path.name != 'stage.py':
        assert all(len(s) <= 100 and s == s.rstrip() for s in path.read_text().splitlines()), path
previous = {}
for directory in sorted(e.HISTORY.iterdir()):
    path = directory/'milestone-manifest.json'
    if path.is_file():
        for name, expected in e.read(path).items():
            assert e.digest(directory/name) == expected, (directory, name)
        previous[directory.name] = e.digest(path)
assert len(previous) == 30
assert previous[e.PILOT.name] == (
    'ae835016813436938e13b67e862effa0d0c1d3ab4af5d24d01310992f764ae84')
for name in ('bridge.py', 'support.py', 'size_repair.py', 'test_repair.py'):
    assert e.digest(here/name) == e.digest(e.PILOT/'verification-tools'/name)
for label, cwd, test in [('pilot', here, 'test_repair'),
    ('evaluator', e.HISTORY/'multibet-group-diagnostic-001/verification-tools', 'test_multi')]:
    result = subprocess.run([sys.executable, '-B', '-W', 'error::ResourceWarning',
        '-m', 'unittest', test, '-v'], cwd=cwd, capture_output=True, timeout=60)
    (here/(label+'-stdout.txt')).write_bytes(result.stdout)
    (here/(label+'-stderr.txt')).write_bytes(result.stderr)
    assert result.returncode == 0, result.stderr.decode()
excluded, historical = e.c.historical_boards()
boards, selection = e.c.select_boards(excluded, per_texture=2)
assert Counter(e.c.texture(b) for b in boards) == {name: 2 for name in e.c.TEXTURES}


def literal_boards(value):
    if type(value) is list:
        if len(value) == 5 and all(type(v) is int and 0 <= v < 52 for v in value):
            if len(set(value)) == 5:
                yield value
        else:
            for child in value:
                yield from literal_boards(child)
    elif type(value) is dict:
        for child in value.values():
            yield from literal_boards(child)


old_boards = [b for path in historical for b in literal_boards(e.read(path))]
old_boards.extend([*e.c.DEVELOPMENT_BOARDS, *e.c.HOLDOUT_BOARDS])
for i, board in enumerate(boards):
    for old in [*old_boards, *boards[:i]]:
        assert all(sorted(4*(v//4)+p[v%4] for v in board) != sorted(old)
                   for p in permutations(range(4)))
e.write(here/'novelty-audit.json', dict(passed=True, fresh_boards=8,
    historical_plans=len(historical), literal_boards_checked=len(old_boards), suit_permutations=24))
# Refresh retained diffs after final report-only corrections; no generated code is executed here.
provenance = e.read(here/'reuse-provenance.json')
for dst, src in [('pilot.py', 'experiment.py'), ('retain.py', 'retain.py')]:
    raw = (e.PILOT/'verification-tools'/src).read_text()
    new = (here/dst).read_text()
    provenance[dst] = dict(source_sha256=e.digest(e.PILOT/'verification-tools'/src),
        generated_sha256=e.digest(here/dst), diff=''.join(difflib.unified_diff(
            raw.splitlines(True), new.splitlines(True),
            fromfile='pilot/'+src, tofile='confirmation/'+dst)))
e.write(here/'reuse-provenance.json', provenance)
git = ['C:/Program Files/Git/cmd/git.exe', '-c', f'safe.directory={e.ROOT}', '-C', str(e.ROOT)]
head = subprocess.check_output(git+['rev-parse', 'HEAD'], text=True).strip()
names = subprocess.check_output(git+['diff', '--name-only'], text=True).splitlines()
e.write(here/'worktree-before.json', dict(head=head, modified_tracked_files={
    name: e.digest(e.ROOT/name) for name in names if (e.ROOT/name).is_file()}))
e.write(here/'preflight.json', dict(passed=True, inherited_tests=9,
    prior_milestones=previous, outcomes_computed=0))
paths = {p.resolve() for p in here.iterdir() if p.is_file()}
paths.update(map(Path, historical))
paths.add(Path(sys.executable).resolve())
paths.add(e.c.MODEL)
for name in previous:
    paths.add(e.HISTORY/name/'milestone-manifest.json')
old_pins = e.read(e.PILOT/'plan.json')['pins']
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
plan = dict(name=e.NAME, output=str(output), boards=boards, excluded_boards=excluded,
    historical_plans=historical, selection_receipt=selection,
    entries=[v for v in e.c.entries_for(boards) if v['bet'] == 5],
    sources=[str(output/'baseline'/f'case-{i:03d}.json') for i in range(16)],
    pins={str(p): e.digest(p) for p in sorted(paths)}, source_head=head,
    phase_timeout_seconds=900, python=sys.version, numpy=e.c.np.__version__,
    scipy=e.c.scipy.__version__, user_words_verbatim="Let's run the confirmation test",
    fitting_tasks=0, fresh_boards=8, frozen_at_utc=datetime.now(timezone.utc).isoformat())
e.bindings(plan)
e.write(here/'plan.json', plan)
e.write(here/'freeze.json', dict(plan_sha256=e.digest(here/'plan.json'), cases=16,
    fresh_boards=8, lp_calls=96, inherited_algorithm_unchanged=True, retained_invoked=False))
print(e.read(here/'freeze.json'))
