"""Exploratory timing continuation after explaining the retained parity refusal."""
import sys
import os
from pathlib import Path
for key in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'):
    os.environ[key]='1'
sys.path[:0]=[str(Path(__file__).parent),'D:/Pontius/.venv/Lib/site-packages',
             'D:/Pontius/tmp/group-opt-author/venv/Lib/site-packages']
import experiment as e

if sys.argv[1]=='prepare':
    e.bindings()
    diagnostic=e.read(e.HERE/'diagnostic.json')
    maxima={a:max(r['reset'][a]['max_abs'] for r in diagnostic['rows'])
            for a in ('policy','regret','accumulator')}
    assert max(maxima.values()) < 1e-10
    e.write(e.HERE/'continuation-plan.json',dict(
        original_plan=e.digest(e.HERE/'plan.json'),
        pins={str(e.HERE/n):e.digest(e.HERE/n) for n in
              ('diagnose.py','diagnostic.json','continue.py')},
        interpretation='Original free-running raise parity FAILED. Exploratory continuation '
        'authorized by the experiment request; not an original-plan pass. No tolerance changed.',
        evidence='From identical CPU input states, 32 individual GPU updates agree within '
        'the original absolute tolerance. Free trajectories amplify reduction rounding '
        'through regret normalization. Preserve both observations.',
        acceptance='Unchanged final quality rule and independent rational certificate. '
        'No adoption or claim of trajectory identity. Timing is exploratory.',
        matched_state_max_abs=maxima))
    print(e.digest(e.HERE/'continuation-plan.json'))
else:
    assert e.digest(e.HERE/'continuation-plan.json')==sys.argv[2]
    amended=e.read(e.HERE/'continuation-plan.json')
    assert e.digest(e.HERE/'plan.json')==amended['original_plan']
    for p,sha in amended['pins'].items():
        assert e.digest(p)==sha
    plan=e.bindings()
    old=e.HISTORY/'full-combo-direct-002/verification-tools'
    sys.path.insert(0,str(old))
    monitor=e.load('continuation_monitor',old/'experiment.py')
    receipts=[]
    def dispatch(label,*args):
        cmd=[e.BASE,'-I','-S','-B','-W','error::ResourceWarning',
             str(e.HERE/'launch.py'),*map(str,args)]
        r=monitor.monitor(cmd,plan,e.HERE/'run',label)
        receipts.append(r)
        assert r['exit']==0 and r['stop_reason'] is None,label
        print('COMPLETE',label,flush=True)
    dispatch('raise-profile','profile','raise')
    for repeat in range(3):
        for case in plan['variants']:
            for arm in (['cpu','gpu'] if repeat%2==0 else ['gpu','cpu']):
                dispatch(f'{case}-{arm}-{repeat}','worker',case,arm,repeat)
    for case in plan['variants']:
        for arm in plan['arms']:
            dispatch(f'{case}-{arm}-verify','verify',case,arm)
        cpu=e.read(e.HERE/'run'/f'{case}-cpu-0.json')['score']['gap']
        for repeat in range(3):
            gpu=e.read(e.HERE/'run'/f'{case}-gpu-{repeat}.json')['score']['gap']
            assert gpu <= cpu*1.01+1e-10
    e.bindings()
    e.write(e.HERE/'run'/'continuation-receipt.json',dict(complete=True,
        original_plan_pass=False, quality_noninferiority_pass=True, receipts=receipts,
        continuation_plan_sha256=sys.argv[2]))
