"""Audit retained development results without any additional optimization."""
from fractions import Fraction as Q
from hashlib import sha256
import importlib.util
import json
from math import fsum
from pathlib import Path

ROOT = Path('D:/Pontius-worktrees/eval-runner-consolidation')
PACKET = ROOT/'docs/research/river-witness-groups-r001'
OUT = Path('D:/Pontius-training/river-abstraction-study/witness-groups-development-001')
EVIDENCE = PACKET/'invocation-001'
read = lambda p: json.loads(p.read_bytes())
digest = lambda p: sha256(p.read_bytes()).hexdigest()
def write(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps(value, sort_keys=True, indent=2)+'\n')
def bounds(v):
    return Q(v['lower_exact']), Q(v['upper_exact'])
def mean(values):
    return tuple(sum(v[k] for v in values)/len(values) for k in (0, 1))

assert read(EVIDENCE/'receipt.json')['exit'] == read(OUT/'receipt.json')['exit'] == 0
assert not (OUT/'failed.json').exists()
manifest = read(OUT/'manifest.json')
assert set(manifest) == {p.name for p in OUT.iterdir() if p.is_file()}-{'manifest.json'}
for name,h in manifest.items():
    assert digest(OUT/name) == h, name
assert (OUT/'plan.json').read_bytes() == (PACKET/'plan.json').read_bytes()
for name,h in read(PACKET/'delivery-manifest.json').items():
    assert digest(PACKET/name) == h, name
for name,h in read(PACKET/'identity.json')['sha256'].items():
    assert digest(ROOT/name) == h, name
spec = importlib.util.spec_from_file_location('screen', ROOT/'tools/river_witness_groups.py')
tool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tool)
import pontius.river_group_optimality as kernel
def forbidden(*args, **kwargs):
    raise AssertionError('No additional LP invocation allowed during result verification')
tool.solve_groups = kernel.linprog = kernel.solve_groups = kernel.solve_seat = forbidden
plan, summary = read(OUT/'plan.json'), read(OUT/'summary.json')
tool.verify_bindings(plan)
assert summary['complete'] is True and summary['candidate_method_cases'] == 4
assert summary['lp_calls_planned'] == 8
assert summary['primary_control'] == 'range_equity' and summary['secondary_control'] == 'range_response'
assert [r['case'] for r in summary['cases']] == tool.IDS

def scalar_bounds(matrix, x, y, groups):
    c,f,a = matrix.check,matrix.fold,matrix.call
    g0,g1 = groups
    low = fsum(float(c[i,j])*(1-x[i]) for i in range(len(x)) for j in range(len(y)))
    low += fsum(min(fsum(x[i]*float(t[i,j]) for i in range(len(x))
                        for j in range(len(y)) if g1[j] == group) for t in (f,a))
                 for group in set(g1))
    high = fsum(max(fsum(float(c[i,j]) for i in range(len(x)) if g0[i] == group
                         for j in range(len(y))),
                    fsum((1-y[j])*float(f[i,j])+y[j]*float(a[i,j])
                         for i in range(len(x)) if g0[i] == group for j in range(len(y))))
                for group in set(g0))
    return low,high

max_feature_error = max_value_error = 0.0
max_width = Q(0)
control_floors = {m: [] for m in tool.METHODS}
candidate_floors = []
case_analysis = []
for case,result in zip(plan['cases'],summary['cases'],strict=True):
    assert result == read(OUT/(case['id']+'.json'))
    matrix,groups,bank = tool.load_case(case, plan)
    tool.verify_record(matrix,groups,bank,result)
    proposal,solution = result['proposal'],result['solution']
    assert proposal['bank_methods'] == list(tool.METHODS)
    assert [len(set(g)) for g in proposal['groups']] == [len(set(g)) for g in groups['uniform_equity_200']]
    c,f,a = matrix.check,matrix.fold,matrix.call
    for player in (0,1):
        for column,record in enumerate(bank['methods']):
            opponent = record['solution'][f'seat{player}']['call' if player == 0 else 'bet']
            for hand in range(96):
                if player == 0:
                    mass = fsum(float(matrix.joint[hand,j]) for j in range(96))
                    delta = fsum((1-opponent[j])*float(f[hand,j])+opponent[j]*float(a[hand,j])
                                 -float(c[hand,j]) for j in range(96))/mass
                else:
                    mass = fsum(float(matrix.joint[i,hand]) for i in range(96))
                    delta = fsum(opponent[i]*(float(f[i,hand])-float(a[i,hand]))
                                 for i in range(96))/mass
                max_feature_error = max(max_feature_error,
                                        abs(delta-proposal['features'][player][hand][column]))
    exact = (list(range(96)),list(range(96)))
    brackets = []
    for player in (0,1):
        record = solution[f'seat{player}']
        lo,hi = bounds(record['value'])
        assert hi-lo == Q(record['gap_exact']) and 0 <= hi-lo <= Q(1,10**8)
        max_width = max(max_width,hi-lo)
        pair = (proposal['groups'][0],exact[1]) if player == 0 else (exact[0],proposal['groups'][1])
        measured = scalar_bounds(matrix,record['bet'],record['call'],pair)
        max_value_error = max(max_value_error,*(abs(x-float(y)) for x,y in zip(measured,(lo,hi))))
        brackets.append((lo,hi))
    (l0,u0),(l1,u1) = brackets
    floor = bounds(solution['minimum_exploitability'])
    assert floor == (max(Q(0),(l1-u0)/2),(u1-l0)/2)
    low,high = scalar_bounds(matrix,solution['seat0']['bet'],solution['seat1']['call'],exact)
    max_value_error = max(max_value_error,abs((high-low)/2-float(floor[1])))
    candidate_floors.append(floor)
    row = dict(case=case['id'], groups=[len(set(g)) for g in proposal['groups']],
               candidate_floor_lower=float(floor[0]), candidate_floor_upper=float(floor[1]),
               controls={})
    for old in bank['methods']:
        name = old['method']
        control = bounds(old['solution']['minimum_exploitability'])
        control_floors[name].append(control)
        expected = (floor[0]-control[1],floor[1]-control[0])
        comparison = result['comparisons'][name]
        assert bounds(comparison) == expected
        classification = 'lower' if expected[1] < 0 else 'higher' if expected[0] > 0 else 'overlapping'
        assert comparison['classification'] == classification
        row['controls'][name] = dict(floor_lower=float(control[0]), floor_upper=float(control[1]),
                                    difference_lower=float(expected[0]), difference_upper=float(expected[1]),
                                    classification=classification)
    case_analysis.append(row)

assert max_feature_error < 1e-12 and max_value_error < 1e-12
assert bounds(summary['minimum_exploitability']) == mean(candidate_floors)
aggregate = {}
for name,floors in control_floors.items():
    control = mean(floors)
    differences = [bounds(r['comparisons'][name]) for r in summary['cases']]
    recorded = summary['comparisons'][name]
    assert bounds(recorded) == mean(differences)
    counts = {label:sum(r['comparisons'][name]['classification']==label for r in summary['cases'])
              for label in ('lower','higher','overlapping')}
    assert recorded['case_counts'] == counts
    midpoint = sum(control)/2
    reduction = None if control[0] == 0 else float(100*(1-(sum(mean(candidate_floors))/2)/midpoint))
    aggregate[name] = dict(control_mean_lower=float(control[0]),control_mean_upper=float(control[1]),
                          candidate_mean_lower=float(mean(candidate_floors)[0]),
                          candidate_mean_upper=float(mean(candidate_floors)[1]),
                          reduction_percent_approx=reduction,case_counts=counts)
tool.verify_bindings(plan)
verification = dict(passed=True, additional_lp_calls=0, result_manifest_members=len(manifest),
    result_manifest_sha256=digest(OUT/'manifest.json'), scalar_feature_entries=3072,
    scalar_asymmetric_certificates=8, scalar_combined_policies=4,
    exact_case_comparisons=16, exact_mean_comparisons=4,
    maximum_feature_discrepancy_chips=max_feature_error,maximum_value_discrepancy_chips=max_value_error,
    maximum_certificate_width_exact=str(max_width),maximum_certificate_width_chips=float(max_width),
    verifier_sha256=digest(Path(__file__)),
    limitation='Independent scalar accumulation reuses reconstructed payoff matrices; not an independent card evaluator. Exact certificate rechecking uses the frozen kernel.')
write(EVIDENCE/'verification.json',verification)
write(EVIDENCE/'analysis.json',dict(aggregate=aggregate,cases=case_analysis,
    interpretation='Oracle-assisted, matched-capacity development screen. Prior witness cost excluded. No fresh holdout or six-max strength claim.'))
print(json.dumps(verification,indent=2))
print(json.dumps(aggregate,indent=2))
print(json.dumps(case_analysis,indent=2))
