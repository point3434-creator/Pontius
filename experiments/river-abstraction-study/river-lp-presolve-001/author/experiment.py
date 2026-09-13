"""One presolve option, six fixed-game workers, unchanged exact acceptance rule."""
from pathlib import Path
import sys
import os
import json
import ctypes as ct
from ctypes import wintypes as wt
import importlib.util
from hashlib import sha256
from time import perf_counter
from datetime import datetime,timezone

HERE=Path(__file__).resolve().parent
ROOT=Path('D:/Pontius-worktrees/eval-runner-consolidation')
HISTORY=ROOT/'experiments/river-abstraction-study'
PRIOR=HISTORY/'river-tree-expansion-001'
OUT=HERE/'run'
sys.path.insert(0,str(PRIOR/'author'))
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
e=load('prior_experiment',PRIOR/'author/experiment.py')
e.OUT=OUT
t=e.t
read=e.d.read
digest=e.d.digest
write=e.write
original_linprog=t.linprog
EXPECTED=dict(time_limit=10,maxiter=20000,
              primal_feasibility_tolerance=1e-9,dual_feasibility_tolerance=1e-9)


def memory():
    info=e.monitor.Memory()
    info.cb=ct.sizeof(info)
    fn=ct.WinDLL('psapi').GetProcessMemoryInfo
    fn.argtypes=[wt.HANDLE,ct.POINTER(e.monitor.Memory),wt.DWORD]
    fn.restype=wt.BOOL
    current=ct.WinDLL('kernel32').GetCurrentProcess
    current.restype=wt.HANDLE
    assert fn(current(),ct.byref(info),info.cb)
    return dict(private_bytes=int(info.PrivateUsage),peak_commit_bytes=int(info.PeakPagefileUsage),
                pid=os.getpid())


def fingerprint(args,kwargs):
    result={}
    for key,value in [('c',args[0])]+[(k,kwargs[k]) for k in ('A_ub','A_eq','b_ub','b_eq')]:
        if e.d.c.scipy.sparse.issparse(value):
            result[key]=dict(shape=list(value.shape),format=value.format,nnz=value.nnz,
                buffers={k:sha256(memoryview(getattr(value,k))).hexdigest()
                         for k in ('data','indices','indptr')})
        else:
            result[key]=dict(shape=list(value.shape),sha256=sha256(memoryview(value)).hexdigest())
    result['bounds']=sha256(json.dumps(kwargs['bounds']).encode()).hexdigest()
    return result


def install(presolve,emit):
    assert type(presolve) is bool
    def call(*args,**kwargs):
        assert kwargs['method']=='highs-ds' and kwargs['options']==EXPECTED
        kwargs['options']=dict(kwargs['options'],presolve=presolve)
        call_id=call.count
        call.count+=1
        emit(dict(event='enter',call=call_id,method=kwargs['method'],options=kwargs['options'],
                  matrix=fingerprint(args,kwargs),memory=memory()))
        start=perf_counter()
        result=original_linprog(*args,**kwargs)
        emit(dict(event='return',call=call_id,status=int(result.status),success=bool(result.success),
                  seconds=perf_counter()-start,memory=memory()))
        return result
    call.count=0
    t.linprog=call


def preflight():
    before=memory()
    allocation=bytearray(128*1024**2)
    after=memory()
    assert after['private_bytes']-before['private_bytes']>=120*1024**2
    del allocation
    # A small actual public tree exercises both option paths and original-game certification.
    record=read(e.d.b.PRIOR/'input-000.json')
    nodes=t.public_tree(record,'checkback')
    sizes,flows=t.sequence_layout(nodes)
    arrays={tuple(n['payoff']):e.np.array([[.125,-.25],[.375,.0625]])*(i+1)
            for i,n in enumerate(nodes) if n['player']==-1}
    rows=[]
    for flag in (True,False):
        events=[]
        install(flag,events.append)
        solution=t.solve(nodes,sizes,flows,arrays)
        assert solution['solver_success']
        probs=t.behavior(nodes,solution['realizations'],2)
        cert=t.certificate(nodes,sizes,arrays,probs)
        assert e.Q(cert['gap'])<=e.Q('1e-8')
        assert len(events)==4
        assert all(x['options']['presolve'] is flag for x in events if x['event']=='enter')
        rows.append(dict(presolve=flag,events=events,certificate=cert))
    assert [v['matrix'] for v in rows[0]['events'] if v['event']=='enter']==[
        v['matrix'] for v in rows[1]['events'] if v['event']=='enter']
    assert max(e.Q(v['certificate']['lower']) for v in rows)<=min(
        e.Q(v['certificate']['upper']) for v in rows)
    t.linprog=original_linprog
    write(HERE/'preflight.json',dict(passed=True,monitor_before=before,monitor_after=after,
                                   tiny_game_arms=rows,lp_calls=4))


def freeze():
    assert read(HERE/'preflight.json')['passed']
    plan=read(PRIOR/'author/plan.json')
    jobs=[]
    for index,order in [(2,(True,False)),(3,(False,True)),(4,(True,False))]:
        for flag in order:
            job=dict(plan['jobs'][index])
            job.update(presolve=flag,label=job['label']+('-on' if flag else '-off'))
            jobs.append(job)
    plan.update(name='river-lp-presolve-001',frozen_at_utc=datetime.now(timezone.utc).isoformat(),
        jobs=jobs,cells=[{k:v for k,v in j.items() if k!='nodes'} for j in jobs],max_lp_calls=12,
        output=str(OUT),decision='six fresh workers; presolve is the only solver change; no retries',
        hypothesis='does disabling presolve reduce native memory enough for a certified solve?',
        acceptance='report all six cells; quality requires independent exact gap <=1e-8; no speed ranking from one pair')
    for p in [Path(__file__),HERE/'preflight.json',PRIOR/'author/experiment.py',
              PRIOR/'author/tree.py',PRIOR/'post-verification/tree.py',
              HISTORY/'river-lp-memory-001/milestone-manifest.json']:
        plan['pins'][str(p)]=digest(p)
    for p in HISTORY.glob('*/milestone-manifest.json'): plan['pins'][str(p)]=digest(p)
    e.bindings(plan)
    write(HERE/'plan.json',plan)
    print(digest(HERE/'plan.json'))


def worker(plan,index):
    job=plan['jobs'][index]
    with (OUT/(job['label']+'-calls.jsonl')).open('x',encoding='utf-8',newline='\n') as stream:
        def emit(row):
            stream.write(json.dumps(row,sort_keys=True)+'\n')
            stream.flush()
        install(job['presolve'],emit)
        e.worker(plan,index)


def verify(plan,index):
    # Previously retained zero-payoff verifier correction; no worker/formulation change.
    e.t=load('corrected_verifier',PRIOR/'post-verification/tree.py')
    e.verify(plan,index)


def run(plan):
    e.bindings(plan)
    OUT.mkdir(exist_ok=False)
    write(OUT/'plan.json',plan)
    start=perf_counter()
    rows=[]
    for index,job in enumerate(plan['jobs']):
        row=dict(label=job['label'],variant=job['variant'],presolve=job['presolve'])
        for mode in ('worker','verify'):
            code=('import sys,runpy;sys.path[:0]='+repr([e.monitor.SITE,str(HERE)])+
                  ';sys.argv=sys.argv[1:];runpy.run_path(sys.argv[0],run_name="__main__")')
            cmd=[e.monitor.BASE_PYTHON,'-I','-S','-B','-W','error::ResourceWarning','-c',code,
                 str(HERE/'experiment.py'),mode,str(index)]
            receipt=e.monitor.monitor(cmd,plan,OUT,job['label']+'-'+mode)
            row[mode]=receipt
            if receipt['exit'] or receipt['stop_reason']: break
            saved=read(OUT/(job['label']+('' if mode=='worker' else '-audit')+'.json'))
            assert saved['executing_pid']==receipt['observed_pid']
            if mode=='worker':
                row.update(solver_success=saved['solution']['solver_success'],
                    strict_pass=saved.get('certificate',{}).get('strict_pass',False),
                    error=saved.get('certificate',{}).get('exploitability'),
                    compute_seconds=saved['setup_seconds']+saved['solve_seconds']+saved.get('certificate_seconds',0))
        rows.append(row)
        print(json.dumps(row),flush=True)
    e.bindings(plan)
    write(OUT/'receipt.json',dict(seconds=perf_counter()-start,rows=rows))


if __name__=='__main__':
    mode=sys.argv[1]
    if mode in ('preflight','freeze'): globals()[mode]()
    else:
        plan=read(HERE/'plan.json')
        if mode=='run':
            assert digest(HERE/'plan.json')==sys.argv[2]
            run(plan)
        else: globals()[mode](plan,int(sys.argv[2]))
