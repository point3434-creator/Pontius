"""Independently reconcile final run outputs and every budget selection."""
from pathlib import Path
from statistics import median
from fractions import Fraction
import hashlib
import json
import sys
sys.path.insert(0,'D:/Pontius/.venv/Lib/site-packages')
import numpy as np
HERE=Path(__file__).parent
OUT=HERE/'run'
def read(p): return json.loads(p.read_text(encoding='utf-8'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,obj):
    with p.open('x',encoding='utf-8',newline='\n') as f:
        json.dump(obj,f,indent=2,sort_keys=True,allow_nan=False)
        f.write('\n')
plan=read(HERE/'plan.json')
receipt=read(OUT/'receipt.json')
assert receipt['complete'] and receipt['campaign_invoked']
assert receipt['plan_sha256']==sha(HERE/'plan.json')
for p,h in plan['pins'].items(): assert sha(Path(p))==h,p
assert len(receipt['receipts'])==31
assert all(r['exit']==0 and r['stop_reason'] is None for r in receipt['receipts'])
summary=read(OUT/'summary.json')
rows=[]
identities={}
for case in plan['variants']:
    for repeat in range(3):
        worker=read(OUT/f'{case}-{repeat}.json')
        wr=read(OUT/f'{case}-{repeat}-receipt.json')
        assert worker['executing_pid']==wr['observed_pid']
        extra=max(0.,wr['seconds']-worker['elapsed_to_close_seconds'])
        previous=None
        for row in worker['checkpoints']:
            stop=row['iterations']
            cert=read(OUT/f'{case}-{repeat}-{stop}-audit.json')
            ar=read(OUT/f'{case}-{repeat}-{stop}-audit-receipt.json')
            assert cert['executing_pid']==ar['observed_pid']
            with np.load(OUT/f'{case}-{repeat}-{stop}-policy.npz') as z:
                h=hashlib.sha256(b''.join(z[k].tobytes() for k in z.files)).hexdigest()
            assert h==row['policy_sha256']==cert['policy_sha256']
            identities.setdefault((case,stop),set()).add(h)
            c=cert['certificate']
            for key in ('value','lower','upper','gap'):
                assert abs(float(Fraction(c[key]))-row['score'][key])<1e-10
            assert Fraction(c['gap'])==Fraction(c['upper'])-Fraction(c['lower'])
            assert Fraction(c['lower'])<=Fraction(c['value'])<=Fraction(c['upper'])
            error=float(Fraction(c['gap'])/2)
            rows.append(dict(case=case,repeat=repeat,iterations=stop,error=error,
                charged_seconds=row['prefix_seconds']+extra+ar['seconds'],
                training_seconds=row['training_seconds'],audit_wall=ar['seconds'],
                strict_pass=c['strict_pass'],regression=previous is not None and error>previous))
            previous=error
assert all(len(h)==1 for h in identities.values())
budgets=[]
for case in plan['variants']:
    for budget in plan['budgets_seconds']:
        choices=[]
        improvements=[]
        for repeat in range(3):
            candidates=[r for r in rows if r['case']==case and r['repeat']==repeat]
            anchor=next(r for r in candidates if r['iterations']==2048)
            affordable=sorted((r for r in candidates if r['charged_seconds']<=budget),
                              key=lambda r:r['iterations'])
            chosen=affordable[-1] if affordable else None
            observed=next(r for r in summary['comparisons']
                          if r['case']==case and r['repeat']==repeat)['selected'][str(budget)]
            assert (None if chosen is None else chosen['iterations'])==(
                None if observed is None else observed['iterations'])
            choices.append(None if chosen is None else chosen['iterations'])
            improvements.append(None if chosen is None else anchor['error']/chosen['error'])
        budgets.append(dict(case=case,budget=budget,selected_iterations=choices,
                            improvement_factors=improvements,coverage=sum(x is not None for x in choices)))
aggregates=[]
for case in plan['variants']:
    for stop in plan['checkpoints']:
        rs=[r for r in rows if r['case']==case and r['iterations']==stop]
        assert len({r['error'] for r in rs})==1
        aggregates.append(dict(case=case,iterations=stop,error=rs[0]['error'],
            training_median=median(r['training_seconds'] for r in rs),
            charged_min=min(r['charged_seconds'] for r in rs),
            charged_median=median(r['charged_seconds'] for r in rs),
            charged_max=max(r['charged_seconds'] for r in rs)))
assessment=dict(complete=True,trajectories=6,audits=24,checkpoint_repeat_identity=True,
    regressions=sum(r['regression'] for r in rows),strict_passes=sum(r['strict_pass'] for r in rows),
    aggregates=aggregates,budgets=budgets,
    summed_child_wall_seconds=sum(r['seconds'] for r in receipt['receipts']),
    peak_private_mib=max(r['sampled_peak_private_bytes'] for r in receipt['receipts'])/2**20)
write(HERE/'assessment.json',assessment)
print(json.dumps(assessment,indent=2))
