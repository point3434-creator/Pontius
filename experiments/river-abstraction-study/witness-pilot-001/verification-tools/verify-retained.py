"""Read-only post-run arithmetic, identity and completeness audit; no solver calls."""
from collections import Counter
from fractions import Fraction as Q
from hashlib import sha256
import json
from pathlib import Path
from statistics import stdev

ROOT = Path('D:/Pontius-worktrees/eval-runner-consolidation')
PACKET = ROOT/'docs/research/river-witness-pilot-r001'
OUT = Path('D:/Pontius-training/river-abstraction-study/witness-pilot-001')
EVIDENCE = PACKET/'invocation-001'
read = lambda p: json.loads(p.read_bytes())
digest = lambda p: sha256(p.read_bytes()).hexdigest()
def write(path,value):
    with path.open('x',encoding='utf-8',newline='\n') as stream:
        stream.write(json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n')
def bounds(v):
    return Q(v['lower_exact']),Q(v['upper_exact'])
def avg(values):
    return tuple(sum(v[k] for v in values)/len(values) for k in (0,1))
def mid(v):
    return float(sum(bounds(v))/2)
def close(a,b):
    assert abs(a-b) < 1e-12,(a,b)

assert read(EVIDENCE/'receipt.json')['exit'] == read(OUT/'receipt.json')['exit'] == 0
assert not (OUT/'failed.json').exists()
manifest = read(OUT/'manifest.json')
assert set(manifest) == {p.name for p in OUT.iterdir() if p.is_file()}-{'manifest.json'}
for name,h in manifest.items():
    assert digest(OUT/name) == h,name
assert (OUT/'plan.json').read_bytes() == (PACKET/'plan.json').read_bytes()
for name,h in read(PACKET/'delivery-manifest.json').items():
    assert digest(PACKET/name) == h,name
for name,h in read(PACKET/'identity.json')['sha256'].items():
    assert digest(ROOT/name) == h,name
plan,summary = read(OUT/'plan.json'),read(OUT/'summary.json')
for name,h in plan['sources'].items():
    assert digest(ROOT/name) == h,name
assert plan['lp_calls'] == summary['lp_calls_planned'] == 480
assert summary['complete'] is True and summary['case_count'] == 48
assert summary['board_units'] == 8
assert summary['primary_control'] == 'range_equity'
assert summary['secondary_control'] == 'range_response'
rows = summary['cases']
assert [r['case'] for r in rows] == plan['cases'] and len(rows) == 48
METHODS = ('exact','uniform_equity_200','range_equity','range_response')
max_gap = Q(0)
for case,row in zip(plan['cases'],rows,strict=True):
    assert row == read(OUT/(case['id']+'.json'))
    controls = row['bank']['methods']
    assert [r['method'] for r in controls] == list(METHODS)
    candidate = row['candidate']
    capacity = [len(set(g)) for g in row['inputs']['groups']['uniform_equity_200']]
    assert [len(set(g)) for g in candidate['proposal']['groups']] == capacity
    assert [len(h) for h in row['inputs']['hands']] == [96,96]
    for control in controls:
        name = control['method']
        if name != 'exact':
            assert [len(set(g)) for g in row['inputs']['groups'][name]] == capacity
        else:
            assert [len(set(g)) for g in row['inputs']['groups'][name]] == [96,96]
    for solution in [r['solution'] for r in controls]+[candidate['solution']]:
        endpoints = []
        for seat in ('seat0','seat1'):
            lo,hi = bounds(solution[seat]['value'])
            assert hi-lo == Q(solution[seat]['gap_exact'])
            assert 0 <= hi-lo <= Q(1,10**8)
            max_gap = max(max_gap,hi-lo)
            endpoints.append((lo,hi))
        (l0,u0),(l1,u1) = endpoints
        assert bounds(solution['minimum_exploitability']) == (max(Q(0),(l1-u0)/2),(u1-l0)/2)
    floor = bounds(candidate['solution']['minimum_exploitability'])
    for control in controls:
        comparison = candidate['comparisons'][control['method']]
        lo,hi = bounds(control['solution']['minimum_exploitability'])
        delta = floor[0]-hi,floor[1]-lo
        assert bounds(comparison) == delta
        assert comparison['classification'] == (
            'lower' if delta[1] < 0 else 'higher' if delta[0] > 0 else 'overlapping')

def check_statistics(selected,record):
    for method in (*METHODS,'witness_advantage'):
        values = [bounds(r['candidate']['solution']['minimum_exploitability'])
            if method == 'witness_advantage' else bounds(next(
                c for c in r['bank']['methods'] if c['method'] == method)
                ['solution']['minimum_exploitability']) for r in selected]
        assert bounds(record['mean_floors'][method]) == avg(values)
    for method in METHODS:
        values = [r['candidate']['comparisons'][method] for r in selected]
        actual = record['comparisons'][method]
        assert bounds(actual) == avg([bounds(v) for v in values])
        counts = Counter(v['classification'] for v in values)
        assert actual['case_counts'] == {k:counts[k] for k in ('lower','higher','overlapping')}
        assert actual['worst_case'] == max(selected,key=lambda r:bounds(
            r['candidate']['comparisons'][method])[1])['case']['id']

check_statistics(rows,summary['overall'])
assert [b['board_index'] for b in summary['boards']] == list(range(8))
for b in summary['boards']:
    selected = [r for r in rows if r['case']['board_index'] == b['board_index']]
    assert len(selected) == 6 and len(b['pool_means']) == 3
    assert b['board'] == selected[0]['case']['board']
    assert b['texture'] == selected[0]['case']['texture']
    check_statistics(selected,b)
    for pool,p in enumerate(b['pool_means']):
        check_statistics([r for r in selected if r['case']['pool'] == pool],p)
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
        check_statistics([r for r in rows if r['case'][key] == value],record)
assert [r['omitted'] for r in summary['leave_one_board_out']] == list(range(8))
for record in summary['leave_one_board_out']:
    check_statistics([r for r in rows if r['case']['board_index'] != record['omitted']],record)
verification = dict(passed=True,additional_lp_calls=0,cases=48,board_units=8,
    floor_interval_identities=240,asymmetric_gap_records=480,case_comparisons=192,
    independent_aggregate_checks='Overall, board, pool, regime, texture, SD and leave-one-board-out.',
    maximum_certificate_width_exact=str(max_gap),maximum_certificate_width_chips=float(max_gap),
    manifest_members=len(manifest),manifest_sha256=digest(OUT/'manifest.json'),
    verifier_sha256=digest(Path(__file__)),
    limitation='Post-run audit checks retained arithmetic and identity. Full game, feature and '
    'certificate reconstruction was performed by the frozen parent before its successful exit; '
    'this audit does not repeat that evaluator or optimization.')
write(EVIDENCE/'verification.json',verification)
floors = summary['overall']['mean_floors']
candidate = mid(floors['witness_advantage'])
analysis = dict(mean_floors={m:mid(v) for m,v in floors.items()},
    reductions_percent={m:100*(1-candidate/mid(floors[m])) if mid(floors[m]) > 1e-12
                        else None for m in METHODS},
    counts={m:summary['overall']['comparisons'][m]['case_counts'] for m in METHODS},
    boards=[dict(index=b['board_index'],board=b['board'],texture=b['texture'],
        candidate=mid(b['mean_floors']['witness_advantage']),
        range_equity=mid(b['mean_floors']['range_equity']),
        range_response=mid(b['mean_floors']['range_response']),
        delta_range_equity=mid(b['comparisons']['range_equity']),
        delta_range_response=mid(b['comparisons']['range_response']),
        pool_sd=b['pool_sd_chips']['range_equity']) for b in summary['boards']],
    lobo_primary=[mid(r['comparisons']['range_equity']) for r in summary['leave_one_board_out']],
    between_board_sd=summary['between_board_sd_chips'],
    worker_seconds=read(OUT/'receipt.json')['seconds'],
    whole_invocation_seconds=read(EVIDENCE/'receipt.json')['seconds'])
write(EVIDENCE/'analysis.json',analysis)
print(json.dumps(verification,indent=2))
print(json.dumps(analysis,indent=2))
