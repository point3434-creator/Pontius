"""Independent fitted-equation, scalar diagnostic and exact-rational result audit."""
from collections import Counter
from fractions import Fraction as Q
from hashlib import sha256
import json
from math import fsum,isclose,isfinite
import os
from pathlib import Path
for name in ('OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','OMP_NUM_THREADS'):os.environ[name]='1'
import numpy as np

OUT=Path('D:/Pontius-training/river-abstraction-study/witness-clipped-target-001')
read=lambda p:json.loads(p.read_bytes())
digest=lambda p:sha256(p.read_bytes()).hexdigest()
bounds=lambda x:(Q(x['lower_exact']),Q(x['upper_exact']))
mid=lambda x:float(sum(bounds(x))/2)
scalar_clip=lambda x:min(.5,max(-.5,x))

def write(path,value):
    with path.open('x',encoding='utf-8',newline='\n') as f:
        f.write(json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n')

def close(a,b):assert isclose(a,b,rel_tol=1e-9,abs_tol=1e-11),(a,b)
def basis(raw):return [1.,*raw,*[raw[i]*raw[j] for i in range(11) for j in range(i,11)]]

assert read(OUT/'receipt.json')['exit']==read(OUT/'worker-receipt.json')['exit']==0
assert read(OUT/'worker-complete.json')==dict(complete=True,cases=48,lp_calls=96)
assert not (OUT/'failed.json').exists()
plan=read(OUT/'plan.json');summary=read(OUT/'summary.json');training=read(OUT/'training.json')
for path,h in plan['pins'].items():assert digest(Path(path))==h,path
manifest=read(OUT/'results-manifest.json')
for name,h in manifest.items():assert digest(OUT/name)==h,name
assert set(manifest)=={p.name for p in OUT.iterdir() if p.is_file()}-{'results-manifest.json','receipt.json'}
assert training['fit_calls']==summary['parent_refit_calls']==2
assert training['target_clip']==.5 and training['alpha']==.001
rows=[read(OUT/(case['id']+'.json')) for case in plan['cases']]
assert [r['case'] for r in rows]==plan['cases']
assert [r['case'] for r in training['training_rows']]==plan['training_cases']
models=training['models']
assert len(models)==2
for m in models:
    assert m['schema']=='quadratic-ridge-witness-v1' and m['alpha']==.001
    assert len(m['coefficients'])==78 and all(len(r)==4 and all(isfinite(v) for v in r)
                                            for r in m['coefficients'])
diagnostic_values=0
for split,selected in [('training',training['training_rows']),('evaluation',rows)]:
    for row in selected:
        saved=read(Path(plan[split])/(row['case']['id']+'.json'))
        teacher=saved if split=='training' else saved['teacher']
        old=read(Path(plan['diagnostic'])/(split+'-'+row['case']['id']+'.json'))
        seats=row['seats'] if split=='training' else row['diagnostics']
        for seat,data in enumerate(seats):
            assert data['raw']==old['seats'][seat]['raw']
            target=teacher['candidate']['proposal']['features'][seat]
            weights=data['weights']; total=fsum(weights)
            assert len(data['raw'])==len(weights)==96 and all(v>0 for v in weights)
            for i in range(96):
                close(weights[i],teacher['candidate']['proposal']['marginals'][seat][i])
                phi=basis(data['raw'][i])
                for c in range(4):
                    assert data['target'][i][c]==scalar_clip(target[i][c])
                    assert data['old_features'][i][c]==scalar_clip(old['seats'][seat]['prediction'][i][c])
                    prediction=fsum(phi[j]*models[seat]['coefficients'][j][c] for j in range(78))
                    close(prediction,data['prediction'][i][c])
                    assert data['features'][i][c]==scalar_clip(data['prediction'][i][c])
                    diagnostic_values+=4
            for method,field in [('new','features'),('old','old_features')]:
                for c in range(4):
                    errors=[data[field][i][c]-data['target'][i][c] for i in range(96)]
                    close(fsum(weights[i]*errors[i]**2 for i in range(96))/total,
                          data['metrics'][method]['mse'][c])
                    close(fsum(weights[i]*abs(errors[i]) for i in range(96))/total,
                          data['metrics'][method]['mae'][c])
        for seat in (0,1):
            for method in ('old','new'):
                for metric in ('mse','mae'):
                    for c in range(4):
                        field='seats' if split=='training' else 'diagnostics'
                        close(fsum(r[field][seat]['metrics'][method][metric][c] for r in selected)/48,
                              summary['prediction_errors'][split][seat][method][metric][c])

residuals=[]
for seat in (0,1):
    design=[];targets=[];weights=[]
    for row in training['training_rows']:
        d=row['seats'][seat]; total=fsum(d['weights'])
        design.extend(basis(x) for x in d['raw']); targets.extend(d['target'])
        weights.extend(w/total/48 for w in d['weights'])
    x,y,w=np.array(design),np.array(targets),np.array(weights)
    b=np.array(models[seat]['coefficients'])
    # Recompute the regularized first-order condition, without calling a solver.
    ridge=.001*b.copy();ridge[0]=0
    residual=x.T@(w[:,None]*(x@b-y))+ridge
    maximum=float(np.max(np.abs(residual)))
    assert maximum<1e-10,maximum
    residuals.append(maximum)

maxgap=Q(0)
for row in rows:
    saved=read(Path(plan['boundary'])/(row['case']['id']+'.json'))
    for name,value in saved['floors'].items():assert row['floors'][name]==value
    reference=read(Path(plan['evaluation'])/(row['case']['id']+'.json'))
    capacity=[len(set(g)) for g in reference['teacher']['inputs']['groups']['uniform_equity_200']]
    method='clipped_target_model';solution=row['solutions'][method]
    assert [len(set(g)) for g in row['groups'][method]]==capacity
    endpoints=[]
    for seat in ('seat0','seat1'):
        lo,hi=bounds(solution[seat]['value'])
        assert hi-lo==Q(solution[seat]['gap_exact']) and 0<=hi-lo<=Q(1,10**8)
        maxgap=max(maxgap,hi-lo);endpoints.append((lo,hi))
    (l0,u0),(l1,u1)=endpoints
    floor=max(Q(0),(l1-u0)/2),(u1-l0)/2
    assert bounds(solution['minimum_exploitability'])==bounds(row['floors'][method])==floor
    for other,c in row['comparisons'][method].items():
        lo,hi=bounds(row['floors'][other]);delta=floor[0]-hi,floor[1]-lo
        assert bounds(c)==delta
        assert c['classification']==('lower' if delta[1]<0 else 'higher' if delta[0]>0 else 'overlapping')

checked=0
def check(selected,actual):
    global checked
    def avg(values):return tuple(sum(v[k] for v in values)/len(values) for k in (0,1))
    for m,value in actual['mean_floors'].items():
        assert bounds(value)==avg([bounds(r['floors'][m]) for r in selected]);checked+=1
    for method,comparisons in actual['comparisons'].items():
        for other,c in comparisons.items():
            values=[r['comparisons'][method][other] for r in selected]
            assert bounds(c)==avg([bounds(v) for v in values])
            assert c['counts']==dict(Counter(v['classification'] for v in values));checked+=1
check(rows,summary['overall'])
for b,s in summary['boards'].items():
    selected=[r for r in rows if r['case']['board_index']==int(b)];assert len(selected)==6
    check(selected,s)
    for p,sub in s['pools'].items():check([r for r in selected if r['case']['pool']==int(p)],sub)
for name,key in [('regimes','regime'),('textures','texture')]:
    for value,s in summary[name].items():check([r for r in rows if r['case'][key]==value],s)
for b,s in summary['leave_one_board_out'].items():
    check([r for r in rows if r['case']['board_index']!=int(b)],s)
verification=dict(passed=True,cases=48,training_cases=48,new_floor_identities=48,asymmetric_gaps=96,
    signed_comparisons=384,aggregate_records=checked,diagnostic_values_checked=diagnostic_values,
    normal_equation_max_residuals=residuals,maximum_certificate_gap=float(maxgap),
    extra_audit_fits=0,extra_audit_lp_calls=0,result_manifest_sha256=digest(OUT/'results-manifest.json'),
    auditor_sha256=digest(Path(__file__)))
write(OUT/'audit.json',verification)
analysis=dict(mean_floors={m:mid(v) for m,v in summary['overall']['mean_floors'].items()},
    comparisons={other:dict(delta=mid(c),counts=c['counts'])
                 for other,c in summary['overall']['comparisons']['clipped_target_model'].items()},
    boards={b:dict(floors={m:mid(v) for m,v in s['mean_floors'].items()},
                   deltas={m:mid(v) for m,v in s['comparisons']['clipped_target_model'].items()})
            for b,s in summary['boards'].items()},
    regimes={name:dict(floors={m:mid(v) for m,v in s['mean_floors'].items()},
                       counts={m:c['counts'] for m,c in s['comparisons']['clipped_target_model'].items()})
        for name,s in summary['regimes'].items()},
    lobo={other:[mid(s['comparisons']['clipped_target_model'][other]) for s in
                summary['leave_one_board_out'].values()] for other in summary['overall']['comparisons']['clipped_target_model']},
    prediction_errors=summary['prediction_errors'],
    preidentified_cases={r['case']['id']:{m:mid(v) for m,v in r['floors'].items()}
        for r in rows if r['case']['id'] in ('b07-p1-polarized','b07-p2-polarized')},
    worker_seconds=read(OUT/'worker-receipt.json')['seconds'],
    worker_plus_parent_seconds=read(OUT/'receipt.json')['seconds'],fit_seconds=training['fit_seconds'],
    training_reconstruction_seconds=training['input_reconstruction_seconds'])
write(OUT/'analysis.json',analysis)
print(json.dumps(verification,indent=2));print(json.dumps(analysis,indent=2))
