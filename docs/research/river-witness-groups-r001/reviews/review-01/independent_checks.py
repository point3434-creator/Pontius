from pathlib import Path
from fractions import Fraction as Q
from itertools import product
from copy import deepcopy
from unittest.mock import patch
import importlib.util, json, sys
import numpy as np
ROOT = Path('D:/Pontius-worktrees/eval-runner-consolidation')
SCRATCH = Path('D:/Pontius/tmp/witness-groups-review-01')
sys.path[:0] = [str(ROOT/'src'), str(ROOT/'tests')]
from pontius.river_abstraction_study import PayoffGame
from pontius import river_witness_groups as w
from pontius import river_group_optimality as o
spec = importlib.util.spec_from_file_location('review_tool', ROOT/'tools/river_witness_groups.py')
tool = importlib.util.module_from_spec(spec); spec.loader.exec_module(tool)

def scalar_features(game, opponents, seat):
    j,c,f,a = game.joint,game.check,game.fold,game.call
    if seat == 0:
        return [[float(sum(((1-Q(float(y[k])))*Q(float(f[i,k])) + Q(float(y[k]))*Q(float(a[i,k])) - Q(float(c[i,k])) for k in range(j.shape[1])), Q(0))/sum((Q(float(v)) for v in j[i,:]),Q(0))) for y in opponents] for i in range(j.shape[0])]
    return [[float(sum((Q(float(x[i]))*(Q(float(f[i,k]))-Q(float(a[i,k]))) for i in range(j.shape[0])),Q(0))/sum((Q(float(v)) for v in j[:,k]),Q(0))) for x in opponents] for k in range(j.shape[1])]

def v(game,x,y):
    total = Q(0)
    for i in range(len(x)):
        for j in range(len(y)):
            xi, yj = Q(float(x[i])), Q(float(y[j]))
            total += (1-xi)*Q(float(game.check[i,j])) + xi*((1-yj)*Q(float(game.fold[i,j])) + yj*Q(float(game.call[i,j])))
    return total

def responses(game,x,y,groups):
    xs = [[p[g] for g in groups[0]] for p in product((0,1), repeat=max(groups[0])+1)]
    ys = [[p[g] for g in groups[1]] for p in product((0,1), repeat=max(groups[1])+1)]
    return min(v(game,x,p) for p in ys),max(v(game,p,y) for p in xs)

rng = np.random.default_rng(70891)
scalar_checks = 0
for shape in [(2,3),(3,2),(3,3)]:
    joint = rng.integers(1,6,size=shape).astype(float)/64
    c,f,a = [joint*rng.integers(-5,6,size=shape) for _ in range(3)]
    game = PayoffGame(joint,c,f,a,None,'review-synthetic')
    for seat in (0,1):
        opponents = [rng.integers(0,5,size=shape[1-seat]).astype(float)/4 for _ in range(4)]
        np.testing.assert_allclose(w.action_advantages(game,opponents,seat), scalar_features(game,opponents,seat), rtol=0,atol=2e-14)
        scalar_checks += 1
        if seat == 1:
            full = w.action_advantages(game,opponents,seat)
            np.testing.assert_allclose(w.action_advantages(game,[x/2 for x in opponents],seat),full/2,rtol=0,atol=2e-14)
            np.testing.assert_array_equal(w.action_advantages(game,[np.zeros(shape[0])],seat),np.zeros((shape[1],1)))

# Four certificates on a dense 3x3 game with different fixed-capacity partitions.
shape=(3,3)
joint=np.array([[1,2,3],[4,2,1],[2,1,4]],dtype=float)/32
c,f,a=[joint*rng.integers(-5,6,size=shape) for _ in range(3)]
game=PayoffGame(joint,c,f,a,None,'review-bank')
groups = dict(exact=([0,1,2],[0,1,2]), uniform_equity_200=([0,0,1],[0,0,1]), range_equity=([0,1,1],[0,1,1]), range_response=([0,1,0],[0,1,0]))
bank=dict(case='synthetic',methods=[dict(method=m,solution=o.solve_groups(game,groups[m])) for m in w.METHODS])
with patch.object(o,'linprog',side_effect=AssertionError('proposal LP forbidden')):
    proposal=w.propose(game,groups,bank)
    assert w.propose(game,groups,bank)==proposal
for seat in (0,1):
    opponents=[row['solution'][f'seat{seat}']['call' if seat==0 else 'bet'] for row in bank['methods']]
    np.testing.assert_allclose(proposal['features'][seat],scalar_features(game,opponents,seat),rtol=0,atol=2e-14)
    wrong=[row['solution'][f'seat{1-seat}']['call' if seat==0 else 'bet'] for row in bank['methods']]
    assert not np.allclose(scalar_features(game,opponents,seat),scalar_features(game,wrong,seat)), 'fixture must distinguish wrong asymmetric source'
assert [len(set(g)) for g in proposal['groups']]==[2,2]
solution=o.solve_groups(game,proposal['groups'])
for seat in (0,1):
    row=solution[f'seat{seat}']; asymmetric=(proposal['groups'][0],[0,1,2]) if seat==0 else ([0,1,2],proposal['groups'][1])
    low,high=responses(game,row['bet'],row['call'],asymmetric)
    assert row['value']['lower_exact']==str(low) and row['value']['upper_exact']==str(high)
    assert high-low<=Q(1,10**8)
low,high=responses(game,solution['seat0']['bet'],solution['seat1']['call'],([0,1,2],[0,1,2]))
assert (high-low)/2==Q(solution['minimum_exploitability']['upper_exact'])

for c,b,expected in [(o.interval(Q(1),Q(2)),o.interval(Q(3),Q(4)),'lower'),(o.interval(Q(3),Q(4)),o.interval(Q(1),Q(2)),'higher'),(o.interval(Q(1),Q(2)),o.interval(Q(2),Q(3)),'overlapping'),(o.interval(Q(1),Q(1)),o.interval(Q(1),Q(1)),'overlapping')]:
    d=w.difference(c,b)
    assert d['classification']==expected
    assert Q(d['lower_exact'])==Q(c['lower_exact'])-Q(b['upper_exact'])
    assert Q(d['upper_exact'])==Q(c['upper_exact'])-Q(b['lower_exact'])

# Reuse the permitted two-hand fixture once, retaining the full genuine smoke outputs.
from test_river_witness_groups import WitnessToolTests
smoke=SCRATCH/'independent-smoke'; smoke.mkdir()
helper=WitnessToolTests(); plan=helper.prepare(tool,smoke)
result=helper.run_plan(tool,smoke,plan)
assert result['complete'] is True
broken=deepcopy(plan); broken['cases'][0]['files']['inputs.json']='0'*64
try:
    tool.verify_bindings(broken)
except ValueError as e:
    assert str(e)=='witness uses different case inputs'
else: raise AssertionError('wrong producer input binding accepted')

# A partial manifest write can leave an invalid file, but cannot return successful completion.
changed=deepcopy(plan); out=smoke/'partial-manifest'; changed['output_directory']=str(out)
original=tool.base.write_json

def partial_write(path,value):
    if path==out/'manifest.json':
        with path.open('x') as f: f.write('{')
        raise OSError('independent partial manifest write failure')
    return original(path,value)
with patch.object(tool.base,'write_json',side_effect=partial_write):
    try: helper.run_plan(tool,smoke,changed,'partial-plan.json')
    except OSError as e: assert str(e)=='independent partial manifest write failure'
    else: raise AssertionError('partial manifest write returned completion')
assert json.loads((out/'failed.json').read_bytes())['complete'] is False
try: json.loads((out/'manifest.json').read_bytes())
except json.JSONDecodeError: pass
else: raise AssertionError('expected partial manifest')

results=dict(passed=True,scalar_feature_checks=scalar_checks,asymmetric_source_checks=2,
 source_swap_fixture_distinguishes_wrong_seat=True,synthetic_candidate_lp_calls=2,synthetic_control_lp_calls=8,
 asymmetric_certificates_enumerated=2,paired_policy_upper_endpoint_exact=True,
 interval_boundary_checks=4,wrong_input_binding_rejected=True,real_two_hand_parent_and_worker_passed=True,
 partial_manifest_error_rejected=True,development_groups_constructed=0,development_lp_calls=0)
with (SCRATCH/'independent-checks.json').open('x') as f: json.dump(results,f,indent=2)
print(json.dumps(results,indent=2))