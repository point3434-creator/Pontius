"""Freeze full-hand comparison after reference and process-bound checks."""
import experiment as e
from datetime import datetime, timezone

assert not (e.HERE/'plan.json').exists()
check = e.subprocess.run([e.sys.executable, '-B', '-W', 'error::ResourceWarning',
    '-m', 'unittest', 'test_direct', '-v'], cwd=e.HERE, capture_output=True, timeout=60)
(e.HERE/'tests-stdout.txt').write_bytes(check.stdout)
(e.HERE/'tests-stderr.txt').write_bytes(check.stderr)
assert check.returncode == 0, check.stderr.decode()
assert e.read(e.HERE/'monitor-check.json') == dict(passed=True, cases=4)
previous = {}
for folder in sorted(e.HISTORY.iterdir()):
    manifest = folder/'milestone-manifest.json'
    if manifest.is_file():
        for member, value in e.read(manifest).items():
            assert e.digest(folder/member) == value
        previous[folder.name] = e.digest(manifest)
assert len(previous) == 34
assert previous[e.PREVIOUS.name] == 'a9991e46fe5970beb9c171a81d181722493aaae1e63b71f4be29b4822be70597'
git = ['C:/Program Files/Git/cmd/git.exe', '-c', f'safe.directory={e.ROOT}', '-C', str(e.ROOT)]
head = e.subprocess.check_output(git+['rev-parse', 'HEAD'], text=True).strip()
names = e.subprocess.check_output(git+['diff', '--name-only'], text=True).splitlines()
e.write(e.HERE/'worktree-before.json', dict(head=head, modified_tracked_files={
    name: e.digest(e.ROOT/name) for name in names if (e.ROOT/name).is_file()}))
n = 1081
sizes = dict(primal_ub=4*n*5*n*8, primal_eq=n*5*n*8, dual_ub=3*n*3*n*8)
assert max(sizes.values()) < 200*1024**2
e.write(e.HERE/'preflight.json', dict(passed=True, tests=3, monitor_checks=4,
    prior_milestones=previous, largest_dense_arrays_bytes=sizes, research_solves=0))
paths = {p.resolve() for p in e.HERE.rglob('*') if p.is_file()}
paths.add(e.Path(e.BASE_PYTHON))
for folder in ('D:/Pontius/tmp/full-combo-direct-author',
               'D:/Pontius-training/river-abstraction-study/full-combo-direct-001'):
    paths.update(p.resolve() for p in e.Path(folder).rglob('*') if p.is_file())
paths.update(p.resolve() for p in e.PREVIOUS.rglob('*') if p.is_file())
paths.update(e.HISTORY/name/'milestone-manifest.json' for name in previous)
for path, value in e.read(e.PREVIOUS/'plan.json')['pins'].items():
    assert e.digest(path) == value
    paths.add(e.Path(path))
out = e.Path('D:/Pontius-training/river-abstraction-study')/e.NAME
assert not out.exists()
plan = dict(name=e.NAME, output=str(out), cases=list(range(4)), source_head=head,
    base_python=e.BASE_PYTHON, site_packages=e.SITE,
    python=e.sys.version, numpy=e.d.np.__version__, scipy=e.d.c.scipy.__version__,
    case_timeout_seconds=120, private_limit_mib=3072,
    user_words_verbatim='lets get some full hand detail and see where we sit',
    frozen_at_utc=datetime.now(timezone.utc).isoformat(),
    pins={str(p): e.digest(p) for p in sorted(paths)})
e.bindings(plan)
e.write(e.HERE/'plan.json', plan)
e.write(e.HERE/'freeze.json', dict(plan_sha256=e.digest(e.HERE/'plan.json'),
    previous_milestones=len(previous), retained_invoked=False))
print(e.read(e.HERE/'freeze.json'))
