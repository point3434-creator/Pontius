"""Recompute fixed-work, preparation and repeated-use comparisons from receipts."""
from pathlib import Path
from statistics import median
from fractions import Fraction
import hashlib
import json
HERE=Path(__file__).parent
OUT=HERE/'run'
def read(p): return json.loads(p.read_text(encoding='utf-8'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,obj):
    with p.open('x',encoding='utf-8',newline='\n') as f:
        json.dump(obj,f,indent=2,sort_keys=True,allow_nan=False)
        f.write('\n')
receipt=read(OUT/'receipt.json')
assert receipt['complete']
assert receipt['plan_sha256']==sha(HERE/'plan.json')
for p,h in read(HERE/'plan.json')['pins'].items(): assert sha(Path(p))==h,p
rows=[]
for case in ('checkback','raise'):
    identities=set()
    for arm in ('eager','static','graph'):
        ds=[read(OUT/f'{case}-{arm}-{r}.json') for r in range(3)]
        rs=[read(OUT/f'{case}-{arm}-{r}-receipt.json') for r in range(3)]
        for d,r in zip(ds,rs):
            assert r['exit']==0 and r['stop_reason'] is None
            assert r['observed_pid']==d['executing_pid']
            identities.update(s['policy_sha256'] for s in d['solves'])
        cert=read(OUT/f'{case}-{arm}-0-certificate.json')
        cr=read(OUT/f'{case}-{arm}-verify-receipt.json')
        assert cr['exit']==0 and cert['executing_pid']==cr['observed_pid']
        for k in ('value','lower','upper','gap'):
            assert abs(float(Fraction(cert['certificate'][k]))-ds[0]['solves'][0]['score'][k])<1e-10
        def preparation(d):
            return sum(d[k] for k in ('transfer_setup_seconds','construction_seconds',
                'warmup_seconds','initial_reset_seconds','capture_seconds'))
        def one(s):
            return sum(s[k] for k in ('reset_seconds','train_seconds',
                'average_transfer_seconds','score_seconds'))
        rows.append(dict(case=case,arm=arm,
            first_solve_median=median(d['solves'][0]['train_seconds'] for d in ds),
            first_solve_range=[min(d['solves'][0]['train_seconds'] for d in ds),
                               max(d['solves'][0]['train_seconds'] for d in ds)],
            reused_solve_median=median(d['solves'][1]['train_seconds'] for d in ds),
            preparation_median=median(preparation(d) for d in ds),
            capture_median=median(d['capture_seconds'] for d in ds),
            reset_median=median(d['solves'][1]['reset_seconds'] for d in ds),
            accounted_first_with_audit=median(preparation(d)+one(d['solves'][0]) for d in ds)+cert['seconds'],
            two_solve_process_wall=median(r['seconds'] for r in rs),
            two_solve_plus_two_fresh_audits=median(r['seconds'] for r in rs)+2*cr['seconds'],
            audit_seconds=cert['seconds'],audit_process_seconds=cr['seconds'],
            host_peak_mib=max(r['sampled_peak_private_bytes'] for r in rs)/2**20,
            gpu_pool_mib=max(d['pool_reserved_bytes'] for d in ds)/2**20,
            exploitability=cert['certificate']['exploitability'],
            strict_pass=cert['certificate']['strict_pass']))
    assert len(identities)==1,case
comparisons=[]
for case in ('checkback','raise'):
    e,s,g=[r for r in rows if r['case']==case]
    saved=s['first_solve_median']-g['first_solve_median']
    comparisons.append(dict(case=case,
        graph_vs_eager=e['first_solve_median']/g['first_solve_median'],
        graph_vs_static=s['first_solve_median']/g['first_solve_median'],
        two_solve_audited_speedup=e['two_solve_plus_two_fresh_audits']/g['two_solve_plus_two_fresh_audits'],
        first_accounted_speedup=e['accounted_first_with_audit']/g['accounted_first_with_audit'],
        capture_only_break_even_iterations=(2048*g['capture_median']/saved if saved>0 else None)))
write(HERE/'assessment.json',dict(complete=True,training_workers=18,solves=36,audits=6,
    all_final_policy_bytes_identical=True,rows=rows,comparisons=comparisons))
print(json.dumps(dict(rows=rows,comparisons=comparisons),indent=2))
