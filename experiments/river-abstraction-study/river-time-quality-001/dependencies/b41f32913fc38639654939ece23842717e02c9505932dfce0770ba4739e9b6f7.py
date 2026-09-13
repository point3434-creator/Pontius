"""Fixed three-arm graph experiment with reused solves and independent CPU audits."""
from time import perf_counter
START=perf_counter()
from pathlib import Path
import sys
import os
import json
import hashlib
import experiment as old
import numpy as np

HERE=Path(__file__).resolve().parent
ARMS=['eager','static','graph']
read,write,digest=old.read,old.write,old.digest


def bindings():
    plan=read(HERE/'plan.json')
    assert sys.version_info[:3]==(3,14,6) and np.__version__=='2.5.2'
    for p,h in plan['pins'].items(): assert digest(p)==h,p
    return plan


def prepare():
    old.bindings()
    pins=dict(read(old.HERE/'plan.json')['pins'])
    for p in HERE.glob('*.py'): pins[str(p)]=digest(p)
    for name in ('experiment.py','gpu_adapter.py','plan.json'):
        pins[str(old.HERE/name)]=digest(old.HERE/name)
    from blas import DLL
    pins[str(DLL)]=digest(DLL)
    write(HERE/'plan.json',dict(name=HERE.name,authorization="User: Let's test it",
        variants=['checkback','raise'],arms=ARMS,repeats=3,solves_per_worker=2,
        iterations=2048,warmup_iterations=32,case_timeout_seconds=180,
        private_limit_mib=3072,gpu_pool_limit_mib=1024,config=old.CONFIG,
        correctness='32 iteration state identical across all three GPU arms; replay/reset/counter gates',
        quality='Final policies bitwise identical across arms, repeats and resets; '
                'independent rational audit of every game/arm repeat-zero first solve',
        timing='Synchronized wall; capture and reset separate; first and reused solve; '
               'process wall covers both solves, outputs and teardown',
        cache='Dedicated filesystem CuPy cache warmed by preflight; first-use preflight retained',
        scope='Two fixed heads-up river trees; same-game reset reuse only; no changed ranges',
        source_commit='6518b9d3af252c93f8a9dbdb13fb28adc2859b4c',pins=pins))
    print(digest(HERE/'plan.json'))


def worker(case,arm,repeat):
    bindings()
    t=perf_counter()
    import cupy as cp
    from gpu_adapter import Solver as Eager
    from static_solver import StaticSolver
    assert cp.__version__=='14.2.0'
    cp.get_default_memory_pool().set_limit(size=1024*2**20)
    spec,host=old.game(case)
    arrays={k:cp.asarray(a) for k,a in host.items()}
    cp.cuda.Stream.null.synchronize()
    transfer_setup=perf_counter()-t
    def construct():
        return (Eager(spec['nodes'],arrays,old.CONFIG) if arm=='eager'
                else StaticSolver(spec['nodes'],arrays,2048))
    t=perf_counter()
    model=construct()
    stream=cp.cuda.Stream.null if arm=='eager' else model.stream
    stream.synchronize()
    construction=perf_counter()-t
    t=perf_counter()
    with stream:
        for _ in range(32): model.step()
    stream.synchronize()
    warmup=perf_counter()-t
    t=perf_counter()
    if arm=='eager': model=construct()
    else:
        with stream: model.reset()
    stream.synchronize()
    initial_reset=perf_counter()-t
    t=perf_counter()
    if arm=='graph': model.capture()
    stream.synchronize()
    capture=perf_counter()-t
    # Capturing records operations; it must not advance either counter.
    assert model.iteration==0
    if arm!='eager': assert int(model.counter.get())==0
    records=[]
    for solve in range(2):
        t=perf_counter()
        if solve:
            if arm=='eager': model=construct()
            else:
                with stream: model.reset()
        stream.synchronize()
        reset=perf_counter()-t
        t=perf_counter()
        with stream:
            for _ in range(2048):
                if arm=='eager': model.step()
                else: model.step(replay=arm=='graph')
        stream.synchronize()
        train=perf_counter()-t
        assert model.iteration==2048
        if arm!='eager': assert int(model.counter.get())==2048
        t=perf_counter()
        avg={k:cp.asnumpy(a) for k,a in model.average().items()}
        cp.cuda.Stream.null.synchronize()
        transfer=perf_counter()-t
        t=perf_counter()
        score=old.Solver(spec['nodes'],host,old.CONFIG).score(avg)
        scoring=perf_counter()-t
        for a in avg.values():
            assert np.isfinite(a).all() and (a>=0).all()
            np.testing.assert_allclose(a.sum(1),1,atol=1e-14,rtol=0)
        policy_sha=hashlib.sha256(b''.join(a.tobytes() for a in avg.values())).hexdigest()
        if solve==0:
            with (HERE/'run'/f'{case}-{arm}-{repeat}-policy.npz').open('xb') as f:
                np.savez(f,**{str(k):a for k,a in avg.items()})
        else: assert policy_sha==records[0]['policy_sha256']
        records.append(dict(train_seconds=train,reset_seconds=reset,
            average_transfer_seconds=transfer,score_seconds=scoring,score=score,
            policy_sha256=policy_sha))
    pool=cp.get_default_memory_pool().total_bytes()
    t=perf_counter()
    if arm!='eager': model.close()
    teardown=perf_counter()-t
    write(HERE/'run'/f'{case}-{arm}-{repeat}.json',dict(executing_pid=os.getpid(),
        case=case,arm=arm,repeat=int(repeat),transfer_setup_seconds=transfer_setup,
        construction_seconds=construction,warmup_seconds=warmup,
        initial_reset_seconds=initial_reset,capture_seconds=capture,
        teardown_seconds=teardown,pool_reserved_bytes=pool,solves=records,
        worker_elapsed_seconds=perf_counter()-START))
    bindings()


def verify(case,arm):
    bindings()
    sys.path.insert(0,str(old.HISTORY/'full-combo-direct-002/verification-tools'))
    tree=old.load('graph_exact_tree',old.HISTORY/'river-tree-expansion-001/author/tree.py')
    spec,arrays=old.game(case)
    label=f'{case}-{arm}-0'
    with np.load(HERE/'run'/f'{label}-policy.npz') as z:
        probs={i:tree.quantize(z[i]) for i in z.files}
    t=perf_counter()
    cert=tree.certificate(spec['nodes'],spec['sizes'],arrays,probs)
    seconds=perf_counter()-t
    score=read(HERE/'run'/f'{label}.json')['solves'][0]['score']
    for key in ('value','lower','upper','gap'):
        assert abs(float(tree.Q(cert[key]))-score[key])<1e-10
    write(HERE/'run'/f'{label}-certificate.json',dict(executing_pid=os.getpid(),
        certificate=cert,seconds=seconds,float_agreement=True))


def run(expected):
    assert digest(HERE/'plan.json')==expected
    plan=bindings()
    out=HERE/'run'
    out.mkdir(exist_ok=False)
    path=old.HISTORY/'full-combo-direct-002/verification-tools'
    sys.path.insert(0,str(path))
    monitor=old.load('graph_monitor',path/'experiment.py')
    receipts=[]
    def dispatch(label,target,*args):
        cmd=[old.BASE,'-I','-S','-B','-W','error::ResourceWarning',
             str(HERE/'launch.py'),target,*map(str,args)]
        r=monitor.monitor(cmd,plan,out,label)
        receipts.append(r)
        assert r['exit']==0 and r['stop_reason'] is None,label
        print('COMPLETE',label,flush=True)
    dispatch('frozen-gates','test_graph.py')
    for repeat in range(3):
        for case in plan['variants']:
            for index in range(3):
                arm=ARMS[(index+repeat)%3]
                dispatch(f'{case}-{arm}-{repeat}','run.py','worker',case,arm,repeat)
    for case in plan['variants']:
        hashes={read(out/f'{case}-{arm}-{r}.json')['solves'][0]['policy_sha256']
                for arm in ARMS for r in range(3)}
        assert len(hashes)==1,case
        for arm in ARMS:
            dispatch(f'{case}-{arm}-verify','run.py','verify',case,arm)
    bindings()
    write(out/'receipt.json',dict(complete=True,plan_sha256=expected,
        all_arms_repeats_resets_policy_identical=True,receipts=receipts))


if __name__=='__main__':
    mode,*args=sys.argv[1:]
    globals()[mode](*args)
