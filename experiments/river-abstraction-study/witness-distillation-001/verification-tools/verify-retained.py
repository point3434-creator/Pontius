"""Independent retained arithmetic and identity audit. Stdlib only; no fits or LPs."""
from collections import Counter
from fractions import Fraction as Q
from hashlib import sha256
import json
from math import isfinite
from pathlib import Path
from statistics import stdev

ROOT = Path('D:/Pontius-worktrees/eval-runner-consolidation')
PACKET = ROOT/'docs/research/river-witness-distillation-r001'
OUT = Path('D:/Pontius-training/river-abstraction-study/witness-distillation-001')
EVIDENCE = PACKET/'invocation-001'
METHODS = ('exact','uniform_equity_200','range_equity','range_response')
read = lambda p: json.loads(p.read_bytes())
digest = lambda p: sha256(p.read_bytes()).hexdigest()

def write(path,value):
    with path.open('x',encoding='utf-8',newline='\n') as f:
        f.write(json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n')

def bounds(v):
    return Q(v['lower_exact']),Q(v['upper_exact'])

def avg(values):
    return tuple(sum(v[k] for v in values)/len(values) for k in (0,1))

def mid(v):
    return float(sum(bounds(v))/2)

def close(a,b):
    assert abs(a-b) < 1e-12,(a,b)

def validate_manifest(root,name,exact=False):
    entries = read(root/name)
    for member,h in entries.items():
        assert digest(root/member) == h,member
    if exact:
        assert set(entries) == {p.name for p in root.iterdir() if p.is_file()}-{name}
    return entries

def compare(a,b,c):
    alo,ahi = bounds(a)
    blo,bhi = bounds(b)
    delta = alo-bhi,ahi-blo
    assert bounds(c) == delta
    assert c['classification'] == (
        'lower' if delta[1] < 0 else 'higher' if delta[0] > 0 else 'overlapping')

def stats(rows,record,candidate_name):
    for method in (*METHODS,candidate_name):
        values = [bounds(r['candidate']['solution']['minimum_exploitability'])
            if method == candidate_name else bounds(next(c for c in r['bank']['methods']
                if c['method'] == method)['solution']['minimum_exploitability']) for r in rows]
        assert bounds(record['mean_floors'][method]) == avg(values)
    for method in METHODS:
        values = [r['candidate']['comparisons'][method] for r in rows]
        actual = record['comparisons'][method]
        assert bounds(actual) == avg([bounds(v) for v in values])
        counts = Counter(v['classification'] for v in values)
        assert actual['case_counts'] == {k:counts[k] for k in ('lower','higher','overlapping')}
        assert actual['worst_case'] == max(rows,key=lambda r:bounds(
            r['candidate']['comparisons'][method])[1])['case']['id']

def panel(rows,summary,candidate_name):
    assert len(rows) == summary['case_count'] == 48
    assert summary['board_units'] == 8 and summary['complete'] is True
    assert rows == summary['cases']
    stats(rows,summary['overall'],candidate_name)
    for b in summary['boards']:
        selected = [r for r in rows if r['case']['board_index'] == b['board_index']]
        assert len(selected) == 6 and len(b['pool_means']) == 3
        stats(selected,b,candidate_name)
        for pool,p in enumerate(b['pool_means']):
            stats([r for r in selected if r['case']['pool'] == pool],p,candidate_name)
        for m in METHODS:
            close(b['pool_sd_chips'][m],stdev(mid(p['comparisons'][m]) for p in b['pool_means']))
    for m in METHODS:
        close(summary['between_board_sd_chips'][m],stdev(
            mid(b['comparisons'][m]) for b in summary['boards']))
        assert bounds(summary['overall']['comparisons'][m]) == avg([
            bounds(b['comparisons'][m]) for b in summary['boards']])
    for field,key in (('by_texture','texture'),('by_regime','regime')):
        assert set(summary[field]) == {r['case'][key] for r in rows}
        for value,record in summary[field].items():
            stats([r for r in rows if r['case'][key] == value],record,candidate_name)
    assert [r['omitted'] for r in summary['leave_one_board_out']] == list(range(8))
    for record in summary['leave_one_board_out']:
        stats([r for r in rows if r['case']['board_index'] != record['omitted']],
              record,candidate_name)

outer = read(EVIDENCE/'receipt.json')
assert outer['exit'] == read(OUT/'receipt.json')['exit'] == 0
assert not (OUT/'failed.json').exists() and not (EVIDENCE/'failed.json').exists()
assert isfinite(outer['whole_command_seconds']) and outer['whole_command_seconds'] > 0
assert outer['binding']['approval'] == read(PACKET/'controller-authorization.json')
assert outer['binding']['plan_sha256'] == digest(PACKET/'plan.json')
assert outer['binding']['recorder_sha256'] == digest(PACKET/'accounting/measure_invocation.py')
assert (EVIDENCE/'stdout.txt').is_file() and (EVIDENCE/'stderr.txt').is_file()
manifest = validate_manifest(OUT,'manifest.json',True)
validate_manifest(PACKET,'delivery-manifest.json')
assert (OUT/'plan.json').read_bytes() == (PACKET/'plan.json').read_bytes()
plan,summary = read(OUT/'plan.json'),read(OUT/'summary.json')
for name,h in read(PACKET/'identity.json')['sha256'].items():
    assert digest(ROOT/name) == h,name
for name,h in plan['sources'].items():
    assert digest(ROOT/name) == h,name
for name,h in plan['training']['files'].items():
    assert digest(Path(plan['training']['directory'])/name) == h,name
assert summary['complete'] is True
assert summary['case_count'] == len(plan['cases']) == 48
assert summary['board_units'] == 8
assert summary['lp_calls_planned'] == plan['lp_calls'] == 576
rows = [read(OUT/(case['id']+'.json')) for case in plan['cases']]
assert [r['case'] for r in rows] == plan['cases']
max_gap = Q(0)
for row in rows:
    teacher,student = row['teacher'],row['student']
    assert teacher['case'] == row['case']
    controls = teacher['bank']['methods']
    assert [c['method'] for c in controls] == list(METHODS)
    capacity = [len(set(g)) for g in teacher['inputs']['groups']['uniform_equity_200']]
    assert [len(h) for h in teacher['inputs']['hands']] == [96,96]
    for candidate in (teacher['candidate'],student):
        assert [len(set(g)) for g in candidate['proposal']['groups']] == capacity
    for solution in [c['solution'] for c in controls]+[
            teacher['candidate']['solution'],student['solution']]:
        endpoints = []
        for seat in ('seat0','seat1'):
            lo,hi = bounds(solution[seat]['value'])
            assert hi-lo == Q(solution[seat]['gap_exact'])
            assert 0 <= hi-lo <= Q(1,10**8)
            max_gap = max(max_gap,hi-lo)
            endpoints.append((lo,hi))
        (l0,u0),(l1,u1) = endpoints
        assert bounds(solution['minimum_exploitability']) == (max(Q(0),(l1-u0)/2),(u1-l0)/2)
    for candidate in (teacher['candidate'],student):
        for control in controls:
            compare(candidate['solution']['minimum_exploitability'],
                    control['solution']['minimum_exploitability'],
                    candidate['comparisons'][control['method']])
    compare(student['solution']['minimum_exploitability'],
            teacher['candidate']['solution']['minimum_exploitability'],
            student['comparisons']['oracle_witness'])

oracle_rows = [r['teacher'] for r in rows]
student_rows = [dict(case=r['case'],inputs=r['teacher']['inputs'],
                    bank=r['teacher']['bank'],candidate=r['student']) for r in rows]
panel(oracle_rows,summary['oracle'],'witness_advantage')
panel(student_rows,summary['student'],'predicted_witness')
comparisons = [r['student']['comparisons']['oracle_witness'] for r in rows]
assert bounds(summary['oracle_gap']) == avg([bounds(c) for c in comparisons])
counts = Counter(c['classification'] for c in comparisons)
assert summary['oracle_gap']['case_counts'] == {
    k:counts[k] for k in ('lower','higher','overlapping')}
for b in summary['oracle_gap']['by_board']:
    assert bounds(b) == avg([bounds(r['student']['comparisons']['oracle_witness'])
        for r in rows if r['case']['board_index'] == b['board_index']])
assert summary['nonimprovement_cases'] == [r['case']['id'] for r in rows if
    bounds(r['student']['comparisons']['range_equity'])[1] >= 0]
for key,value in summary['seconds'].items():
    assert isfinite(value) and value >= 0
    assert value == sum(r['seconds'][key] for r in rows)
assert summary['training'] == read(OUT/'models.json')
assert summary['equity_preparation_seconds'] == read(OUT/'preparation.json')['equity_seconds']
assert summary['prediction_errors'] == [dict(case=r['case']['id'],
    seats=r['student']['prediction_error']) for r in rows]

verification = dict(passed=True,additional_lp_calls=0,additional_fits=0,cases=48,board_units=8,
    floor_identities=288,asymmetric_gap_records=576,case_comparisons=432,
    aggregate_checks='Both panels: overall, board, pool, regime, texture, SD, leave-one-board-out; oracle gap.',
    maximum_certificate_width_exact=str(max_gap),maximum_certificate_width_chips=float(max_gap),
    manifest_members=len(manifest),manifest_sha256=digest(OUT/'manifest.json'),
    verifier_sha256=digest(Path(__file__)),
    limitation='Post-run retained arithmetic/identity audit. Frozen parent independently refit models '
    'and reconstructed games/features/certificates before successful exit; no repeat optimization.')
write(EVIDENCE/'verification.json',verification)
student,oracle = summary['student'],summary['oracle']
floors = student['overall']['mean_floors']
predicted = mid(floors['predicted_witness'])
analysis = dict(mean_floors={m:mid(v) for m,v in floors.items()},
    oracle_witness_floor=mid(oracle['overall']['mean_floors']['witness_advantage']),
    reductions_percent={m:100*(1-predicted/mid(floors[m])) for m in METHODS[1:]},
    counts={m:student['overall']['comparisons'][m]['case_counts'] for m in METHODS},
    oracle_gap=mid(summary['oracle_gap']),oracle_gap_counts=summary['oracle_gap']['case_counts'],
    boards=[dict(index=b['board_index'],board=b['board'],texture=b['texture'],
        floors={m:mid(v) for m,v in b['mean_floors'].items()},
        primary_delta=mid(b['comparisons']['range_equity']),
        response_delta=mid(b['comparisons']['range_response'])) for b in student['boards']],
    regimes={k:dict(floors={m:mid(v) for m,v in r['mean_floors'].items()},
                   primary_counts=r['comparisons']['range_equity']['case_counts'])
             for k,r in student['by_regime'].items()},
    lobo_primary=[mid(r['comparisons']['range_equity']) for r in student['leave_one_board_out']],
    nonimprovement_cases=summary['nonimprovement_cases'],
    seconds=summary['seconds'],equity_preparation_seconds=summary['equity_preparation_seconds'],
    training_validation_seconds=summary['training']['validation_seconds'],
    fit_seconds=summary['training']['fit_seconds'],
    worker_seconds=read(OUT/'receipt.json')['seconds'],whole_command_seconds=outer['whole_command_seconds'])
write(EVIDENCE/'analysis.json',analysis)
print(json.dumps(verification,indent=2))
print(json.dumps(analysis,indent=2))
