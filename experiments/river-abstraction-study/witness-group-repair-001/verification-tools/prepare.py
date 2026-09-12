"""Synthetic checks and immutable plan preparation before the authorized invocation."""
from datetime import datetime, timezone
from fractions import Fraction as Q
import ast
from pathlib import Path
import subprocess
import sys
from time import perf_counter
import experiment as e
from environment import np, core, PayoffGame

here = Path(__file__).resolve().parent
if (here/'plan.json').exists():
    raise FileExistsError('freeze already exists')
for path in here.glob('*.py'):
    ast.parse(path.read_bytes())
    bad = [(n, len(line)) for n, line in enumerate(path.read_text().splitlines(), 1)
           if len(line) > 100 or line != line.rstrip()]
    if bad:
        raise ValueError((path.name, bad))
result = subprocess.run([sys.executable, '-B', '-W', 'error::ResourceWarning',
                         '-m', 'unittest', 'test_repair', 'test_runner', '-v'],
                        cwd=here, capture_output=True, timeout=60)
(here/'checks-stdout.txt').write_bytes(result.stdout)
(here/'checks-stderr.txt').write_bytes(result.stderr)
if result.returncode:
    raise RuntimeError('author checks failed')

rng = np.random.default_rng(8711)
j = rng.integers(1, 4, (96, 96)).astype(float)
j /= j.sum()
sign = rng.integers(-1, 2, (96, 96))
m = PayoffGame(j, j*sign*5, j*5, j*sign*10, None, 'synthetic-96')
groups = [(np.arange(96) % 16).tolist()]*2
baseline = core.solve(m, e.weights(groups))
start = perf_counter()
proposal = e.repair.propose(m, groups, baseline)
proposal_seconds = perf_counter()-start
start = perf_counter()
for seat in (0, 1):
    changes = [Q(v) for v in proposal['seats'][seat]['weighted_advantages_exact']]
    independent = e.independent_exchange(groups[seat], changes)
    assert all(proposal['seats'][seat][k] == v for k, v in independent.items())
verification_seconds = perf_counter()-start
e.write(here/'preflight.json', dict(passed=True, tests=10,
    synthetic_shape=[96, 96], groups_per_seat=16, scored_research_panel=False,
    proposal_seconds=proposal_seconds, independent_enumeration_seconds=verification_seconds,
    meaning='Synthetic timing only; not a production runtime guarantee.'))

git = ['C:/Program Files/Git/cmd/git.exe', '-c', f'safe.directory={e.ROOT}', '-C', str(e.ROOT)]
head = subprocess.check_output(git+['rev-parse', 'HEAD'], text=True).strip()
names = subprocess.check_output(git+['diff', '--name-only'], text=True).splitlines()
e.write(here/'worktree-before.json', dict(head=head, modified_tracked_files={
    name: e.digest(e.ROOT/name) for name in names if (e.ROOT/name).is_file()}))
output = Path('D:/Pontius-training/river-abstraction-study')/e.NAME
if output.exists():
    raise FileExistsError('retained output already exists')
plan = e.make_plan(output)
plan['user_words_verbatim'] = 'sorry bad idea. what do you suggest next lets build it and ru it'
plan['authority'] = 'User explicitly requested selection, building and running of the next test.'
plan['source_head'] = head
plan['frozen_at_utc'] = datetime.now(timezone.utc).isoformat()
for path in here.iterdir():
    if path.is_file() and path.name not in ('plan.json', 'freeze.json'):
        plan['pins'][str(path)] = e.digest(path)
e.bindings(plan)
e.write(here/'plan.json', plan)
e.write(here/'freeze.json', dict(plan_sha256=e.digest(here/'plan.json'),
    pinned_files=len(plan['pins']), cases=32, lp_calls=64, trajectories=64,
    worker_and_verifier_timeout_seconds=900, hard_rss_cap=None,
    retained_output_exists=output.exists(), retained_invoked=False))
print(e.read(here/'freeze.json'))
