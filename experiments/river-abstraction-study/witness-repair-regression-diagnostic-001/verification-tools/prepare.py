"""Validate and freeze a retrospective diagnostic over both complete panels."""
from datetime import datetime, timezone
from pathlib import Path
import ast
import subprocess
import sys
import diagnostic as d

here = Path(__file__).resolve().parent
assert not (here/'plan.json').exists()
for path in here.glob('*.py'):
    ast.parse(path.read_bytes())
    assert all(len(s) <= 100 and s == s.rstrip() for s in path.read_text().splitlines()), path
previous = {}
for directory in sorted(d.HISTORY.iterdir()):
    path = directory/'milestone-manifest.json'
    if path.is_file():
        for name, expected in d.read(path).items():
            assert d.digest(directory/name) == expected, (directory, name)
        previous[directory.name] = d.digest(path)
assert len(previous) == 22
assert previous['witness-group-repair-confirmation-001'] == (
    '9520a603c28c27333d3bba246c7459587f8ea5edd9eac5153e3d33ccf28dbbee')
check = subprocess.run([sys.executable, '-B', '-W', 'error::ResourceWarning',
    '-m', 'unittest', 'test_diagnostic', '-v'], cwd=here, capture_output=True, timeout=60)
(here/'checks-stdout.txt').write_bytes(check.stdout)
(here/'checks-stderr.txt').write_bytes(check.stderr)
assert check.returncode == 0
row = d.read(d.HISTORY/'witness-group-repair-001/case-000.json')
matrix, groups, _ = d.c.build_case(row['entry'])
assert groups == row['baseline_groups']
result = d.analyze(row, matrix)
d.write(here/'preflight.json', dict(passed=True, analytic_checks=5,
    observed_pilot_cells_exercised=1, selected_gate_rules_before_preflight=True,
    retrospective=True, prior_milestones=previous))
git = ['C:/Program Files/Git/cmd/git.exe', '-c', f'safe.directory={d.ROOT}', '-C', str(d.ROOT)]
head = subprocess.check_output(git+['rev-parse', 'HEAD'], text=True).strip()
names = subprocess.check_output(git+['diff', '--name-only'], text=True).splitlines()
d.write(here/'worktree-before.json', dict(head=head, modified_tracked_files={
    name: d.digest(d.ROOT/name) for name in names if (d.ROOT/name).is_file()}))
paths = {p.resolve() for p in here.iterdir() if p.is_file()}
paths.add(Path(sys.executable).resolve())
paths.add(d.c.MODEL)
cases = []
for panel, name, count in [('pilot', 'witness-group-repair-001', 32),
                         ('confirmation', 'witness-group-repair-confirmation-001', 64)]:
    for i in range(count):
        path = d.HISTORY/name/f'case-{i:03d}.json'
        cases.append(dict(panel=panel, path=str(path)))
        paths.add(path)
        if panel == 'pilot':
            paths.add(Path(d.read(path)['entry']['original']))
for name in previous:
    paths.add(d.HISTORY/name/'milestone-manifest.json')
for module in tuple(sys.modules.values()):
    file = getattr(module, '__file__', None)
    if file:
        file = Path(file).resolve()
        if file.suffix == '.py' and file.is_relative_to(d.ROOT):
            paths.add(file)
output = Path('D:/Pontius-training/river-abstraction-study')/d.NAME
assert not output.exists()
plan = dict(name=d.NAME, cases=cases, output=str(output), timeout_seconds=600,
    pins={str(p): d.digest(p) for p in sorted(paths)}, python=sys.version,
    numpy=d.c.np.__version__, scipy=d.c.scipy.__version__, source_head=head,
    user_words_verbatim="Let's investigate that you like a Sherlock Holmes no wonder "
                        'you helped solve that millennium problem',
    authority='User approved the proposed investigation of regressions and acceptance checks.',
    retrospective=True, new_lp_calls=0, training_updates=0,
    frozen_at_utc=datetime.now(timezone.utc).isoformat())
d.bindings(plan)
d.write(here/'plan.json', plan)
d.write(here/'freeze.json', dict(plan_sha256=d.digest(here/'plan.json'), cases=96,
    pinned_files=len(plan['pins']), retained_invoked=False, retrospective=True))
print(d.read(here/'freeze.json'))
