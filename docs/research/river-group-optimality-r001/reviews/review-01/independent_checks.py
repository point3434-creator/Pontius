from fractions import Fraction as Q
from itertools import product
from pathlib import Path
from hashlib import sha256
from unittest.mock import patch
import importlib.util
import json
import os
import sys
import numpy as np
import scipy
from scipy.optimize import linprog
from pontius.river_abstraction_study import PayoffGame
from pontius.river_group_optimality import solve_groups, saddle_bounds, compare_saved

ROOT = Path('D:/Pontius-worktrees/eval-runner-consolidation')
SCRATCH = Path('D:/Pontius/tmp/group-optimality-review-01')
def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result

tool = module('review_tool', ROOT/'tools/river_group_optimality.py')
tests = module('review_test_fixtures', ROOT/'tests/test_river_group_optimality.py')
print('ENVIRONMENT', sys.executable, sys.version, np.__version__, scipy.__version__)
assert sys.version_info[:3] == (3,14,6) and np.__version__ == '2.5.2' and scipy.__version__ == '1.18.0'
assert os.environ['PYTHONDONTWRITEBYTECODE'] == '1'

def vertices(groups):
    return [[Q(p[g]) for g in groups] for p in product((0,1), repeat=max(groups)+1)]

def value(matrix, x, y):
    return sum(((1-x[i])*Q(float(matrix.check[i,j])) + x[i]*(1-y[j])*Q(float(matrix.fold[i,j])) + x[i]*y[j]*Q(float(matrix.call[i,j])) for i in range(len(x)) for j in range(len(y))), Q(0))

def normal_form_interval(matrix, gx, gy):
    # Pure information-set strategies, simplex mixture LPs: independent representation.
    xs, ys = vertices(gx), vertices(gy)
    exact = [[value(matrix,x,y) for y in ys] for x in xs]
    a = np.array(exact, dtype=float)
    m,n = a.shape
    p = linprog(np.r_[np.zeros(m),-1], A_ub=np.c_[-a.T,np.ones(n)], b_ub=np.zeros(n), A_eq=[[*np.ones(m),0]], b_eq=[1], bounds=[(0,None)]*m+[(None,None)], method='highs-ds')
    q = linprog(np.r_[np.zeros(n),1], A_ub=np.c_[a,-np.ones(m)], b_ub=np.zeros(m), A_eq=[[*np.ones(n),0]], b_eq=[1], bounds=[(0,None)]*n+[(None,None)], method='highs-ds')
    assert p.success and q.success
    px = [Q(float(z)) for z in p.x[:m]]; qy = [Q(float(z)) for z in q.x[:n]]
    px = [z/sum(px) for z in px]; qy = [z/sum(qy) for z in qy]
    assert min(px+qy) >= 0
    low = min(sum((px[i]*exact[i][j] for i in range(m)),Q(0)) for j in range(n))
    high = max(sum((qy[j]*exact[i][j] for j in range(n)),Q(0)) for i in range(m))
    assert 0 <= high-low <= Q(1,10**8)
    return low, high

rng = np.random.default_rng(871321)
count = 0
for n0,n1 in [(1,1),(2,3),(3,2),(3,3)]:
    for trial in range(3):
        arrays = [rng.integers(-20,21,size=(n0,n1)).astype(float)/8 for _ in range(3)]
        matrix = PayoffGame(np.ones((n0,n1))/(n0*n1),*arrays,None,'review-synthetic')
        group_pairs = [(list(range(n0)),list(range(n1))),([0]*n0,[0]*n1),([i%2 for i in range(n0)],[j%2 for j in range(n1)])]
        for g0,g1 in group_pairs:
            result = solve_groups(matrix,(g0,g1))
            for seat,(gx,gy) in enumerate([(g0,list(range(n1))),(list(range(n0)),g1)]):
                row = result[f'seat{seat}']
                x,y = [[Q(float(z)) for z in row[k]] for k in ('bet','call')]
                low = min(value(matrix,x,v) for v in vertices(gy))
                high = max(value(matrix,v,y) for v in vertices(gx))
                assert (low,high) == saddle_bounds(matrix,row['bet'],row['call'],(gx,gy))
                independent_low,independent_high = normal_form_interval(matrix,gx,gy)
                assert max(low,independent_low) <= min(high,independent_high)
            x = [Q(float(z)) for z in result['seat0']['bet']]
            y = [Q(float(z)) for z in result['seat1']['call']]
            paired = (max(value(matrix,v,y) for v in vertices(list(range(n0))))-min(value(matrix,x,v) for v in vertices(list(range(n1)))))/2
            assert paired == Q(result['minimum_exploitability']['upper_exact'])
            saved_x = [(g+1)/4 for g in g0]; saved_y = [(g+1)/4 for g in g1]
            comparison = compare_saved(matrix,(g0,g1),result,saved_x,saved_y)
            sx,sy = [Q(v) for v in saved_x],[Q(v) for v in saved_y]
            e = (max(value(matrix,v,sy) for v in vertices(list(range(n0))))-min(value(matrix,sx,v) for v in vertices(list(range(n1)))))/2
            assert Q(comparison['saved_exploitability_exact']) == e
            count += 1
print('SYNTHETIC',count,'group-games; 72 asymmetric certificates cross-checked against exact pure-strategy enumeration and independent simplex normal-form LP certificates')

plan_path = ROOT/'docs/research/river-group-optimality-r001/plan.json'
raw,plan = tool.read_plan(plan_path,'de07461ea9364a4fb40d0bce72a506549bc30ac609761bb0bc57ff4600c3b11c')
reconciled=[]
with patch.object(tool,'solve_groups',side_effect=AssertionError('Observed optimization prohibited')):
    for case in plan['cases']:
        matrix,groups,records=tool.load_case(case,hands=96,steps=[100,1000,10000])
        reconciled.append(dict(case=case['id'],shape=list(matrix.joint.shape),records=len(records),capacities={m:[len(set(g)) for g in pair] for m,pair in groups.items()}))
print('OBSERVED DATA ONLY',json.dumps(reconciled,sort_keys=True))

helper=tests.DiagnosticToolTests()
helper.tool=tool
helper.fixture_files(SCRATCH/'smoke-input')
smoke_plan=tool.make_plan(SCRATCH/'smoke-output',smoke_directory=SCRATCH/'smoke-input')
smoke_path=SCRATCH/'smoke-plan.json'
tool.write_json(smoke_path,smoke_plan)
smoke_digest=sha256(smoke_path.read_bytes()).hexdigest()
summary=tool.execute_plan(smoke_path,smoke_digest)
manifest=tool.read(SCRATCH/'smoke-output/manifest.json')
assert all(sha256((SCRATCH/'smoke-output'/name).read_bytes()).hexdigest()==digest for name,digest in manifest.items())
assert summary['complete'] and summary['verified_saved_profiles']==4
print('PERSISTENT REAL SMOKE',smoke_digest,'manifest',sha256((SCRATCH/'smoke-output/manifest.json').read_bytes()).hexdigest())

# Rebind each edited two-hand fixture, so validation reaches semantic checks.
import copy
original={n:tool.read(SCRATCH/'smoke-input'/n) for n in tool.FILES if n!='manifest.json'}
mutations=[
 ('lift',lambda d:d['result.json']['records'][0].update(hand_bet=[0.9,0.5])),
 ('metric',lambda d:d['result.json']['records'][0]['full_game'].update(value=999)),
 ('joint',lambda d:d['inputs.json']['joint'][0].__setitem__(0,0.9)),
 ('exact_groups',lambda d:d['inputs.json']['groups'].__setitem__('exact',[[0,0],[0,0]])),
 ('checkpoint',lambda d:d['result.json']['records'][0].update(iteration=11)),
 ('capacity',lambda d:d['inputs.json']['groups'].__setitem__('range_response',[[0,0],[0,0]])),
]
for label,mutation in mutations:
    directory=SCRATCH/('invalid-'+label); directory.mkdir()
    data=copy.deepcopy(original); mutation(data)
    for name,record in data.items():tool.write_json(directory/name,record)
    tool.write_json(directory/'manifest.json',{name:sha256((directory/name).read_bytes()).hexdigest() for name in data})
    try:tool.load_case(tool.bind_case('smoke',directory),hands=2,steps=[10])
    except ValueError as error:print('SEMANTIC REJECTION',label,str(error))
    else:raise AssertionError(label+' was accepted')

# Successful worker with rejected parent certificate must not publish a manifest.
from types import SimpleNamespace
for kind in ('certificate','summary-write','manifest-write'):
    output=SCRATCH/('failure-'+kind)
    failure_plan=tool.make_plan(output,smoke_directory=SCRATCH/'smoke-input')
    path=SCRATCH/('failure-plan-'+kind+'.json');tool.write_json(path,failure_plan)
    digest=sha256(path.read_bytes()).hexdigest()
    saved_result=tool.read(SCRATCH/'smoke-output/smoke.json')
    if kind=='certificate':saved_result['methods'][0]['solution']['seat0']['bet']=[0,0]
    def fake_worker(*args,**kwargs):
        tool.write_json(output/'smoke.json',saved_result)
        return SimpleNamespace(returncode=0,stdout=b'',stderr=b'')
    original_write=tool.write_json
    def controlled_write(path,value):
        if kind.endswith('-write') and path.name==kind.removesuffix('-write')+'.json':raise OSError('review injected evidence write failure')
        return original_write(path,value)
    with patch.object(tool.subprocess,'run',side_effect=fake_worker),patch.object(tool,'write_json',side_effect=controlled_write):
        try:tool.execute_plan(path,digest)
        except (ValueError,OSError) as error:print('PARENT FAILURE',kind,type(error).__name__,str(error))
        else:raise AssertionError(kind+' completed')
    assert not (output/'manifest.json').exists()
    assert tool.read(output/'failed.json')['complete'] is False
print('ALL SUPPLEMENTAL CHECKS PASSED')
