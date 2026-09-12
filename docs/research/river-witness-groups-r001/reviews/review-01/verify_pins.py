from pathlib import Path
from hashlib import sha256
import importlib.util, json, subprocess, sys
from unittest.mock import patch
ROOT = Path('D:/Pontius-worktrees/eval-runner-consolidation')
SCRATCH = Path('D:/Pontius/tmp/witness-groups-review-01')
PACKET = ROOT/'docs/research/river-witness-groups-r001'
def digest(p): return sha256(p.read_bytes()).hexdigest()
identity = json.loads((PACKET/'identity.json').read_bytes())
plan = json.loads((PACKET/'plan.json').read_bytes())
pins = {}
for name, expected in identity['sha256'].items():
    actual = digest(ROOT/name); assert actual == expected, name
    pins[str(ROOT/name)] = actual
assert digest(PACKET/'plan.json') == identity['plan_sha256']
for name, expected in identity['predecessor_metadata'].items():
    previous = PACKET/'predecessor-metadata'/name
    assert digest(previous) == expected, str(previous)
    pins[str(previous)] = expected
    if name == 'tests/cases.json':
        old = json.loads(previous.read_bytes()); current = json.loads((ROOT/name).read_bytes())
        assert [x for x in current if x != 'test_river_witness_groups'] == old
    else:
        old = previous.read_text(); current = (ROOT/name).read_text()
        assert current.startswith(old)
        assert current[len(old):].strip().splitlines() == [
            '/src/pontius/river_witness_groups.py -text',
            '/tools/river_witness_groups.py -text',
            '/tests/test_river_witness_groups.py -text']
for name, expected in plan['sources'].items():
    actual = digest(ROOT/name); assert actual == expected, name
    pins[str(ROOT/name)] = actual
for case in plan['cases']:
    for name, expected in case['files'].items():
        path = Path(case['directory'])/name
        assert digest(path) == expected, str(path); pins[str(path)] = expected
    path = Path(case['witness_file'])
    assert digest(path) == case['witness_sha256']; pins[str(path)] = digest(path)
for key in ['witness_manifest', 'witness_plan']:
    path = Path(plan[key]['path'])
    assert digest(path) == plan[key]['sha256']; pins[str(path)] = digest(path)
spec = importlib.util.spec_from_file_location('review_witness_tool', ROOT/'tools/river_witness_groups.py')
tool = importlib.util.module_from_spec(spec); spec.loader.exec_module(tool)
with patch('pontius.river_group_optimality.linprog', side_effect=AssertionError('saved-case LP forbidden')), patch('pontius.river_witness_groups.anchored_clusters', side_effect=AssertionError('saved-case groups forbidden')):
    tool.verify_bindings(plan)
git = 'C:/Program Files/Git/cmd/git.exe'
def git_read(*args):
    return subprocess.check_output([git, '-c', f'safe.directory={ROOT.as_posix()}', '-C', str(ROOT), *args], text=True).strip()
assert git_read('rev-parse','HEAD') == identity['base_commit']
assert git_read('branch','--show-current') == identity['branch']
result = dict(passed=True, python=sys.version, executable=sys.executable,
 numpy=tool.base.np.__version__, scipy=tool.base.scipy.__version__,
 base_commit=identity['base_commit'], branch=identity['branch'], identity_sha256=digest(PACKET/'identity.json'),
 plan_sha256=digest(PACKET/'plan.json'), inventory_sha256=digest(SCRATCH/'inventory.md'),
 pins=pins, identity_file_count=len(identity['sha256']), source_count=len(plan['sources']),
 input_count=sum(len(c['files']) for c in plan['cases']), witness_case_count=len(plan['cases']),
 development_groups_constructed=0, development_lp_calls=0,
 metadata_preservation='predecessor tests and attributes preserved with only new entries appended')
out = SCRATCH/sys.argv[1]
with out.open('x') as f: json.dump(result, f, indent=2)
print(json.dumps({k:v for k,v in result.items() if k != 'pins'}, indent=2))