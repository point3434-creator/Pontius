"""Independent scalar recomputation of all vectorized diagnostic summaries."""
from hashlib import sha256
import json
import math
from pathlib import Path

OUT=Path('D:/Pontius-training/river-abstraction-study/witness-fit-diagnostic-001')
read=lambda p:json.loads(p.read_bytes())
digest=lambda p:sha256(p.read_bytes()).hexdigest()
assert read(OUT/'receipt.json')['exit']==0 and not (OUT/'failed.json').exists()
plan=read(OUT/'plan.json')
for path,h in plan['pins'].items(): assert digest(Path(path))==h,path
for name,h in read(OUT/'results-manifest.json').items(): assert digest(OUT/name)==h,name
s=read(OUT/'summary.json')
assert s['complete'] is True
rows={split:[read(OUT/(split+'-'+case['id']+'.json'))
             for case in read(Path(plan[split])/'plan.json')['cases']]
      for split in ('training','evaluation')}
assert all(len(r)==48 for r in rows.values())
assert [r['case'] for r in rows['training']]==read(Path(plan['training'])/'plan.json')['cases']
assert [r['case'] for r in rows['evaluation']]==read(Path(plan['evaluation'])/'plan.json')['cases']

def close(a,b):
    if a is None or b is None: assert a is b,(a,b)
    else: assert math.isclose(a,b,rel_tol=1e-9,abs_tol=1e-10),(a,b)

for seat in (0,1):
    for col in range(4):
        baseline=math.fsum(math.fsum(h['weights'][i]*h['target'][i][col]
            for i in range(96)) for h in [r['seats'][seat] for r in rows['training']])/48
        close(baseline,s['training_mean_constants'][seat][col])

def scalar(observations,constant):
    total=math.fsum(w for y,p,w in observations)
    data=[(y,p,w/total) for y,p,w in observations]
    weighted=lambda fn:math.fsum(w*fn(y,p) for y,p,w in data)
    mse=weighted(lambda y,p:(p-y)**2)
    baseline=weighted(lambda y,p:(y-constant)**2)
    ym,pm=weighted(lambda y,p:y),weighted(lambda y,p:p)
    yvar,pvar=weighted(lambda y,p:(y-ym)**2),weighted(lambda y,p:(p-pm)**2)
    active=lambda y:abs(y)>1e-10
    wrong=lambda y,p:active(y) and ((y>0)!=(p>0))
    cost=lambda y,p:(y if y>0 else 0)-(y if p>0 else 0)
    mass=weighted(lambda y,p:active(y))
    result=dict(mse=mse,mae=weighted(lambda y,p:abs(p-y)),bias=weighted(lambda y,p:p-y),
        baseline_mse=baseline,skill_vs_training_mean=1-mse/baseline if baseline>0 else None,
        target_mean=ym,prediction_mean=pm,target_sd=math.sqrt(yvar),prediction_sd=math.sqrt(pvar),
        correlation=weighted(lambda y,p:(y-ym)*(p-pm))/math.sqrt(yvar*pvar) if yvar*pvar>0 else None,
        active_mass=mass,sign_mismatch_active=weighted(wrong)/mass if mass else None,
        opportunity_cost=weighted(cost),bands={})
    for name,predicate in [('near_0_to_0.1',lambda y:abs(y)<=.1),
        ('middle_0.1_to_0.5',lambda y:.1<abs(y)<=.5),('far_over_0.5',lambda y:abs(y)>.5)]:
        mass=weighted(lambda y,p:predicate(y))
        act=weighted(lambda y,p:predicate(y) and active(y))
        result['bands'][name]=dict(mass=mass,mse=weighted(lambda y,p:(p-y)**2*predicate(y))/mass
            if mass else None,opportunity_cost=weighted(lambda y,p:cost(y,p)*predicate(y))/mass
            if mass else None,active_mass=act,
            sign_mismatch_active=weighted(lambda y,p:wrong(y,p) and predicate(y))/act if act else None)
    return result

metric_count=0
def check(selected,record):
    global metric_count
    for seat in (0,1):
        for col in range(4):
            observations=[]
            for r in selected:
                h=r['seats'][seat]
                assert len(h['target'])==len(h['prediction'])==len(h['weights'])==96
                close(sum(h['weights']),1)
                observations.extend((y[col],p[col],w/len(selected)) for y,p,w in
                    zip(h['target'],h['prediction'],h['weights'],strict=True))
            expected=scalar(observations,s['training_mean_constants'][seat][col])
            actual=record[seat][col]
            assert expected.keys()==actual.keys()
            for key in expected:
                if key=='bands':
                    for band,values in expected[key].items():
                        for k,value in values.items():
                            close(value,actual[key][band][k]); metric_count+=1
                else:
                    close(expected[key],actual[key]); metric_count+=1

for split,panel in s['panels'].items():
    check(rows[split],panel['overall'])
    for board,record in panel['boards'].items():
        check([r for r in rows[split] if r['case']['board_index']==int(board)],record)
    for regime,record in panel['regimes'].items():
        check([r for r in rows[split] if r['case']['regime']==regime],record)
receipt=dict(passed=True,cases=96,metric_values_checked=metric_count,
    method='Independent stdlib scalar sums from retained hand arrays; no production metrics import.',
    extra_fits=0,extra_lp_calls=0,extra_prediction_calls=0,auditor_sha256=digest(Path(__file__)))
with (OUT/'audit.json').open('x',encoding='utf-8',newline='\n') as f:
    f.write(json.dumps(receipt,sort_keys=True,indent=2)+'\n')
print(json.dumps(receipt))
for split,panel in s['panels'].items():
    print(split)
    for seat,columns in enumerate(panel['overall']):
        for col,m in enumerate(columns):
            print(json.dumps(dict(seat=seat,column=col,mse=m['mse'],
                baseline_skill=m['skill_vs_training_mean'],correlation=m['correlation'],
                prediction_sd=m['prediction_sd'],target_sd=m['target_sd'],
                sign_error=m['sign_mismatch_active'],opportunity_cost=m['opportunity_cost'],
                bands=m['bands'])))
