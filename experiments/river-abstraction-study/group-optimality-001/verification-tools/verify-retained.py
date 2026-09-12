"""Read-only result audit and arithmetic analysis; never invokes an optimizer."""
from fractions import Fraction as Q
from hashlib import sha256
import importlib.util
import json
from math import fsum
from pathlib import Path
import sys

ROOT = Path('D:/Pontius-worktrees/eval-runner-consolidation')
PACKET = ROOT / 'docs/research/river-group-optimality-r001'
OUT = Path('D:/Pontius-training/river-abstraction-study/group-optimality-001')
EVIDENCE = PACKET / 'invocation-001'
read = lambda p: json.loads(p.read_bytes())
digest = lambda p: sha256(p.read_bytes()).hexdigest()
def write(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps(value, sort_keys=True, indent=2) + '\n')

plan, summary = read(OUT/'plan.json'), read(OUT/'summary.json')
assert read(EVIDENCE/'receipt.json')['exit'] == read(OUT/'receipt.json')['exit'] == 0
assert summary['complete'] is True and summary['verified_method_cases'] == 32
assert summary['verified_saved_profiles'] == 96
assert not (OUT/'failed.json').exists()
manifest = read(OUT/'manifest.json')
assert set(manifest) == {p.name for p in OUT.iterdir() if p.is_file()} - {'manifest.json'}
for name, h in manifest.items():
    assert digest(OUT/name) == h, name
assert (OUT/'plan.json').read_bytes() == (PACKET/'plan.json').read_bytes()
preserved = read(PACKET/'delivery-manifest.json')
for name, h in preserved.items():
    assert digest(PACKET/name) == h, name
identity = read(PACKET/'identity.json')
for name, h in identity['sha256'].items():
    assert digest(ROOT/name) == h, name

spec = importlib.util.spec_from_file_location('bound_tool', ROOT/'tools/river_group_optimality.py')
tool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tool)
import pontius.river_group_optimality as kernel
def forbidden(*args, **kwargs):
    raise AssertionError('No optimization authorized in verification')
kernel.linprog = kernel.solve_groups = kernel.solve_seat = tool.solve_groups = forbidden
tool.verify_bindings(plan)

def endpoints(value):
    return Q(value['lower_exact']), Q(value['upper_exact'])

def response_bounds(matrix, x, y, groups):
    c, f, a = matrix.check, matrix.fold, matrix.call
    g0, g1 = groups
    lower = fsum(float(c[i,j])*(1-x[i]) for i in range(len(x)) for j in range(len(y)))
    lower += fsum(min(fsum(x[i]*float(t[i,j]) for i in range(len(x))
                           for j in range(len(y)) if g1[j] == group) for t in (f,a))
                  for group in set(g1))
    upper = fsum(max(fsum(float(c[i,j]) for i in range(len(x)) if g0[i] == group
                         for j in range(len(y))),
                     fsum((1-y[j])*float(f[i,j])+y[j]*float(a[i,j])
                          for i in range(len(x)) if g0[i] == group for j in range(len(y))))
                  for group in set(g0))
    return lower, upper

max_error = 0.0
max_width = Q(0)
rows = []
for case, result in zip(plan['cases'], summary['cases'], strict=True):
    assert result == read(OUT/(case['id']+'.json'))
    assert result['case'] == case['id']
    matrix, groups, saved = tool.load_case(case, hands=96, steps=plan['steps'])
    exact = (list(range(96)), list(range(96)))
    for method in result['methods']:
        name, solution = method['method'], method['solution']
        pair = groups[name]
        brackets = []
        for seat in (0,1):
            record = solution[f'seat{seat}']
            asymmetric = (pair[0],exact[1]) if seat == 0 else (exact[0],pair[1])
            low, high = endpoints(record['value'])
            assert high-low == Q(record['gap_exact']) and 0 <= high-low <= Q(1,10**8)
            max_width = max(max_width, high-low)
            measured = response_bounds(matrix, record['bet'], record['call'], asymmetric)
            max_error = max(max_error, *(abs(v-float(q)) for v,q in zip(measured,(low,high))))
            brackets.append((low,high))
        (l0,u0),(l1,u1) = brackets
        floor = endpoints(solution['minimum_exploitability'])
        assert floor == (max(Q(0),(l1-u0)/2),(u1-l0)/2)
        low,high = response_bounds(matrix, solution['seat0']['bet'], solution['seat1']['call'], exact)
        max_error = max(max_error, abs((high-low)/2-float(floor[1])))
        for profile in method['saved']:
            original = next(r for r in saved if r['method']==name and r['iteration']==profile['iteration'])
            low,high = response_bounds(matrix, original['hand_bet'], original['hand_call'], exact)
            value = Q(profile['saved_exploitability_exact'])
            max_error = max(max_error, abs((high-low)/2-float(value)))
            assert endpoints(profile['avoidable_gap']) == (max(Q(0),value-floor[1]),value-floor[0])
        headline = next(s for s in method['saved'] if s['iteration']==10000)
        rows.append(dict(case=case['id'], method=name,
            floor_lower=float(floor[0]), floor_upper=float(floor[1]),
            saved=float(Q(headline['saved_exploitability_exact'])),
            avoidable_lower=float(endpoints(headline['avoidable_gap'])[0]),
            avoidable_upper=float(endpoints(headline['avoidable_gap'])[1])))
assert max_error < 1e-12, max_error

cohorts = {}
for cohort, methods in summary['cohorts'].items():
    cohorts[cohort] = {}
    for name, aggregate in methods.items():
        selected = [next(m for m in r['methods'] if m['method']==name)
                    for r in summary['cases'] if r['case'].startswith(cohort+'-')]
        assert len(selected) == 4
        floors = [endpoints(m['solution']['minimum_exploitability']) for m in selected]
        assert endpoints(aggregate['minimum_exploitability']) == tuple(sum(f[k] for f in floors)/4 for k in (0,1))
        for step, checkpoint in aggregate['checkpoints'].items():
            profiles = [next(s for s in m['saved'] if s['iteration']==int(step)) for m in selected]
            assert Q(checkpoint['saved_exact']) == sum(Q(s['saved_exploitability_exact']) for s in profiles)/4
            assert endpoints(checkpoint['avoidable_gap']) == tuple(sum(endpoints(s['avoidable_gap'])[k]
                                                                      for s in profiles)/4 for k in (0,1))
        floor = endpoints(aggregate['minimum_exploitability'])
        saved = Q(aggregate['checkpoints']['10000']['saved_exact'])
        cohorts[cohort][name] = dict(floor_lower=float(floor[0]), floor_upper=float(floor[1]),
            saved=float(saved), avoidable=float(saved-(floor[0]+floor[1])/2),
            floor_share_percent=float(100*(floor[0]+floor[1])/2/saved))
    c = cohorts[cohort]
    print(cohort, json.dumps(c, indent=2))
    print('response floor vs range-equity percent', 100*(c['range_response']['floor_upper']/c['range_equity']['floor_upper']-1))
    print('response floor reduction vs baseline percent', 100*(1-c['range_response']['floor_upper']/c['uniform_equity_200']['floor_upper']))

tool.verify_bindings(plan)
verification = dict(pass_=True, optimization_calls=0, manifest_members=len(manifest),
    preserved_packet_members=len(preserved), pinned_identity_members=len(identity['sha256']),
    pinned_source_members=len(plan['sources']), pinned_input_members=32,
    scalar_saddle_pairs=64, scalar_combined_policies=32, scalar_saved_profiles=96,
    max_scalar_discrepancy_chips=max_error, maximum_certificate_width_exact=str(max_width),
    maximum_certificate_width_chips=float(max_width),
    exact_aggregate_checks=32, result_manifest_sha256=digest(OUT/'manifest.json'),
    verification_script_sha256=digest(Path(__file__)),
    limitation='Independent scalar accumulation reuses reconstructed PayoffGame matrices; not an independent card evaluator. The bound parent reverified exact rational certificates.')
write(EVIDENCE/'verification.json', verification)
write(EVIDENCE/'analysis.json', dict(cohorts=cohorts, cases=rows,
    scope='All eight cases already observed; fixed 10000-iteration headline; chips, not BB/100.'))
print(json.dumps(verification, indent=2))
print(json.dumps(rows, indent=2))
