"""Independent scalar/rational audit of the retained boundary-resolution experiment."""
from collections import Counter
from fractions import Fraction as Q
from hashlib import sha256
import json
from math import isfinite
from pathlib import Path

OUT=Path('D:/Pontius-training/river-abstraction-study/witness-boundary-001')
read=lambda p:json.loads(p.read_bytes())
digest=lambda p:sha256(p.read_bytes()).hexdigest()
bounds=lambda x:(Q(x['lower_exact']),Q(x['upper_exact']))
mid=lambda x:float(sum(bounds(x))/2)

def write(path,value):
    with path.open('x',encoding='utf-8',newline='\n') as f:
        f.write(json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n')

assert read(OUT/'receipt.json')['exit']==read(OUT/'worker-receipt.json')['exit']==0
assert read(OUT/'worker-complete.json')==dict(complete=True,cases=48,lp_calls=192)
assert not (OUT/'failed.json').exists()
plan=read(OUT/'plan.json'); summary=read(OUT/'summary.json')
for path,h in plan['pins'].items(): assert digest(Path(path))==h,path
manifest=read(OUT/'results-manifest.json')
for name,h in manifest.items(): assert digest(OUT/name)==h,name
assert set(manifest)=={p.name for p in OUT.iterdir() if p.is_file()}-{'results-manifest.json','receipt.json'}
assert summary['complete'] is True and summary['new_lp_calls']==192 and summary['cases']==48

assert read(OUT/'transform.json')==dict(clip_magnitude=.5)

rows=[read(OUT/(case['id']+'.json')) for case in plan['cases']]
assert [r['case'] for r in rows]==plan['cases']
maxgap=Q(0)
clipped_values=0
transform_diagnostics=[]
for row in rows:
    saved=read(Path(plan['evaluation'])/(row['case']['id']+'.json'))
    old={c['method']:c['solution']['minimum_exploitability'] for c in saved['teacher']['bank']['methods']}
    old['direct_witness']=saved['teacher']['candidate']['solution']['minimum_exploitability']
    old['predicted_only']=saved['student']['solution']['minimum_exploitability']
    for name,value in old.items(): assert row['floors'][name]==value
    for method,original in (
        ('clipped_oracle',saved['teacher']['candidate']['proposal']['features']),
        ('clipped_prediction',saved['student']['proposal']['features'])):
        for seat in (0,1):
            transformed=row['features'][method][seat]
            assert len(original[seat])==len(transformed)==96
            saturated=0
            for before,after in zip(original[seat],transformed,strict=True):
                assert len(before)==len(after)==4
                for value,actual in zip(before,after,strict=True):
                    assert isfinite(value) and actual==min(.5,max(-.5,value))
                    assert (value>0)-(value<0)==(actual>0)-(actual<0)
                    saturated+=int(abs(value)>.5)
                    clipped_values+=1
            transform_diagnostics.append(dict(case=row['case']['id'],method=method,seat=seat,
                saturated_entries=saturated,total_entries=384,
                original_distinct_vectors=len({tuple(v) for v in original[seat]}),
                clipped_distinct_vectors=len({tuple(v) for v in transformed})))
    capacity=[len(set(g)) for g in saved['teacher']['inputs']['groups']['uniform_equity_200']]
    for method in ('clipped_oracle','clipped_prediction'):
        assert [len(set(g)) for g in row['groups'][method]]==capacity
        solution=row['solutions'][method]
        endpoint=[]
        for seat in ('seat0','seat1'):
            lo,hi=bounds(solution[seat]['value'])
            assert hi-lo==Q(solution[seat]['gap_exact']) and 0<=hi-lo<=Q(1,10**8)
            maxgap=max(maxgap,hi-lo); endpoint.append((lo,hi))
        (l0,u0),(l1,u1)=endpoint
        floor=(max(Q(0),(l1-u0)/2),(u1-l0)/2)
        assert bounds(solution['minimum_exploitability'])==bounds(row['floors'][method])==floor
        for other,c in row['comparisons'][method].items():
            lo,hi=bounds(row['floors'][other])
            delta=floor[0]-hi,floor[1]-lo
            assert bounds(c)==delta
            assert c['classification']==('lower' if delta[1]<0 else 'higher' if delta[0]>0 else 'overlapping')

checked=0
def check(selected,actual):
    global checked
    def avg(values): return tuple(sum(v[k] for v in values)/len(values) for k in (0,1))
    for method,value in actual['mean_floors'].items():
        assert bounds(value)==avg([bounds(r['floors'][method]) for r in selected]); checked+=1
    for method,comparisons in actual['comparisons'].items():
        for other,c in comparisons.items():
            values=[r['comparisons'][method][other] for r in selected]
            assert bounds(c)==avg([bounds(v) for v in values])
            assert c['counts']==dict(Counter(v['classification'] for v in values)); checked+=1

check(rows,summary['overall'])
for b,s in summary['boards'].items():
    selected=[r for r in rows if r['case']['board_index']==int(b)]
    assert len(selected)==6
    check(selected,s)
    for p,sub in s['pools'].items(): check([r for r in selected if r['case']['pool']==int(p)],sub)
for name,key in [('regimes','regime'),('textures','texture')]:
    for value,s in summary[name].items(): check([r for r in rows if r['case'][key]==value],s)
for b,s in summary['leave_one_board_out'].items():
    check([r for r in rows if r['case']['board_index']!=int(b)],s)
verification=dict(passed=True,cases=48,new_floor_identities=96,asymmetric_gaps=192,
    signed_comparisons=672,aggregate_records=checked,clipped_values_independently_verified=clipped_values,
    maximum_certificate_gap=float(maxgap),new_audit_lp_calls=0,new_audit_fits=0,
    result_manifest_sha256=digest(OUT/'results-manifest.json'),auditor_sha256=digest(Path(__file__)))
write(OUT/'audit.json',verification)
analysis=dict(mean_floors={m:mid(v) for m,v in summary['overall']['mean_floors'].items()},
    comparisons={m:{other:dict(delta=mid(c),counts=c['counts']) for other,c in cols.items()}
                 for m,cols in summary['overall']['comparisons'].items()},
    boards={b:dict(floors={m:mid(v) for m,v in s['mean_floors'].items()},
                   deltas={method:{m:mid(v) for m,v in cols.items()}
                           for method,cols in s['comparisons'].items()})
            for b,s in summary['boards'].items()},
    regimes={name:dict(floors={m:mid(v) for m,v in s['mean_floors'].items()},
        counts={method:{m:c['counts'] for m,c in cols.items()}
                for method,cols in s['comparisons'].items()})
        for name,s in summary['regimes'].items()},
    lobo={method:{other:[mid(s['comparisons'][method][other])
                        for s in summary['leave_one_board_out'].values()]
                  for other in summary['overall']['comparisons'][method]}
          for method in ('clipped_oracle','clipped_prediction')},
    worker_seconds=read(OUT/'worker-receipt.json')['seconds'],
    worker_plus_parent_seconds=read(OUT/'receipt.json')['seconds'],
    transform_diagnostics=transform_diagnostics)
write(OUT/'analysis.json',analysis)
print(json.dumps(verification,indent=2))
print(json.dumps({k:v for k,v in analysis.items() if k!='transform_diagnostics'},indent=2))
