"""Recompute every reported result from retained worker outputs and receipts."""
import json
from pathlib import Path
from statistics import median
from fractions import Fraction
import hashlib

HERE=Path(__file__).parent
def read(p): return json.loads(p.read_text(encoding='utf-8'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,obj):
    with p.open('x',encoding='utf-8',newline='\n') as f:
        json.dump(obj,f,indent=2,sort_keys=True,allow_nan=False)
        f.write('\n')

run=HERE/'run'
complete=read(run/'continuation-receipt.json')
assert complete['complete'] and not complete['original_plan_pass']
plan=read(HERE/'plan.json')
assert sha(HERE/'plan.json')==read(HERE/'continuation-plan.json')['original_plan']
for p,h in plan['pins'].items(): assert sha(Path(p))==h,p
assert read(run/'raise-parity-receipt.json')['exit']!=0
assert read(run/'checkback-parity.json')['passed']
rows=[]
for case in ('checkback','raise'):
    for arm in ('cpu','gpu'):
        data=[read(run/f'{case}-{arm}-{r}.json') for r in range(3)]
        receipts=[read(run/f'{case}-{arm}-{r}-receipt.json') for r in range(3)]
        for d,r in zip(data,receipts):
            assert r['exit']==0 and r['stop_reason'] is None
            assert d['executing_pid']==r['observed_pid']
        cert=read(run/f'{case}-{arm}-0-certificate.json')
        cr=read(run/f'{case}-{arm}-verify-receipt.json')
        assert cr['exit']==0 and cr['stop_reason'] is None
        assert cert['executing_pid']==cr['observed_pid']
        for k in ('value','lower','upper','gap'):
            assert abs(float(Fraction(cert['certificate'][k]))-data[0]['score'][k])<1e-10
        identity=len({d['policy_sha256'] for d in data})==1
        assert identity, 'If repeats differ, independently audit all policies before reporting'
        row=dict(case=case,arm=arm,train_median=median(d['train_seconds'] for d in data),
            train_min=min(d['train_seconds'] for d in data),
            train_max=max(d['train_seconds'] for d in data),
            process_wall_median=median(r['seconds'] for r in receipts),
            host_private_peak_mib=max(r['sampled_peak_private_bytes'] for r in receipts)/2**20,
            gpu_pool_reserved_mib=max(d['pool_reserved_bytes'] for d in data)/2**20,
            setup_median=median(d['gpu_setup_seconds'] for d in data),
            warmup_median=median(d['warmup_seconds'] for d in data),
            transfer_median=median(d['average_transfer_seconds'] for d in data),
            exact_audit_seconds=cert['seconds'],exact_audit_process_seconds=cr['seconds'],
            audit_peak_private_mib=cr['sampled_peak_private_bytes']/2**20,
            exploitability=cert['certificate']['exploitability'],
            strict_pass=cert['certificate']['strict_pass'], repeat_policies_identical=identity)
        row['solve_plus_separate_audit_wall']=row['process_wall_median']+cr['seconds']
        rows.append(row)
comparisons=[]
for case in ('checkback','raise'):
    cpu,gpu=[r for r in rows if r['case']==case]
    assert gpu['exploitability']<=cpu['exploitability']*1.01+5e-11
    comparisons.append(dict(case=case,train_speedup=cpu['train_median']/gpu['train_median'],
        process_speedup=cpu['process_wall_median']/gpu['process_wall_median'],
        audited_speedup=cpu['solve_plus_separate_audit_wall']/gpu['solve_plus_separate_audit_wall'],
        cpu_matrix_share=read(run/f'{case}-profile.json')['matrix_share'],
        absolute_error_difference=abs(cpu['exploitability']-gpu['exploitability'])))
write(HERE/'assessment.json',dict(complete=True,original_parity_gate_pass=False,
    exploratory_continuation_pass=True,training_runs=12,independent_audits=4,
    rows=rows,comparisons=comparisons))
print(json.dumps(dict(rows=rows,comparisons=comparisons),indent=2))
