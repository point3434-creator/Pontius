"""OS memory observations at frozen Python/native LP boundaries; no allocation tracer."""
from pathlib import Path
import sys
import os
import json
import ctypes as ct
from ctypes import wintypes as wt
import importlib.util
from time import perf_counter
from hashlib import sha256
from datetime import datetime,timezone
import numpy as np
from scipy import sparse

ROOT=Path('D:/Pontius-worktrees/eval-runner-consolidation')
HISTORY=ROOT/'experiments/river-abstraction-study'
PRIOR=HISTORY/'river-tree-expansion-001'
HERE=Path(__file__).resolve().parent
OUT=HERE/'run'
sys.path.insert(0,str(PRIOR/'author'))
spec=importlib.util.spec_from_file_location('frozen_tree_experiment',PRIOR/'author/experiment.py')
e=importlib.util.module_from_spec(spec)
spec.loader.exec_module(e)
e.OUT=OUT


def memory():
    info=e.monitor.Memory()
    info.cb=ct.sizeof(info)
    fn=ct.WinDLL('psapi').GetProcessMemoryInfo
    fn.argtypes=[wt.HANDLE,ct.POINTER(e.monitor.Memory),wt.DWORD]
    fn.restype=wt.BOOL
    current=ct.WinDLL('kernel32').GetCurrentProcess
    current.restype=wt.HANDLE
    assert fn(current(),ct.byref(info),info.cb)
    return dict(private_bytes=int(info.PrivateUsage),working_bytes=int(info.WorkingSetSize),
        peak_commit_bytes=int(info.PeakPagefileUsage),pid=os.getpid())


def visible_buffers(frame):
    result={}
    for name,value in frame.f_locals.items():
        if isinstance(value,np.ndarray):
            result[name]=dict(kind='ndarray',shape=list(value.shape),bytes=value.nbytes)
        elif sparse.issparse(value):
            buffers=[getattr(value,k) for k in ('data','indices','indptr','row','col') if hasattr(value,k)]
            unique={(v.__array_interface__['data'][0],v.nbytes) for v in buffers}
            result[name]=dict(kind=value.format,shape=list(value.shape),nnz=value.nnz,
                             bytes=sum(n for address,n in unique))
    return result


def trace_sources():
    import scipy.optimize._linprog_highs as highs
    import scipy.optimize._linprog_util as util
    import scipy.optimize._highspy._highs_wrapper as wrapper
    return [Path(e.t.__file__),Path(highs.__file__),Path(util.__file__),Path(wrapper.__file__)]


def traced_worker(index):
    sources={os.path.normcase(str(p.resolve())):p.read_text().splitlines() for p in trace_sources()}
    functions={'solve','_linprog_highs','_clean_inputs','_format_A_constraints','_highs_wrapper'}
    started=perf_counter()
    job=plan['prior_plan']['jobs'][index]
    with (OUT/(job['label']+'-trace.jsonl')).open('x',encoding='utf-8',newline='\n') as stream:
        def emit(frame,event):
            source=sources[os.path.normcase(frame.f_code.co_filename)]
            row=dict(event=event,file=frame.f_code.co_filename,function=frame.f_code.co_name,
                line=frame.f_lineno,source_line=source[frame.f_lineno-1].strip(),
                elapsed=perf_counter()-started,memory=memory(),buffers=visible_buffers(frame))
            ancestor=frame
            while ancestor is not None:
                if ancestor.f_code.co_name=='solve' and 'role' in ancestor.f_locals:
                    row['role']=ancestor.f_locals['role']
                    break
                ancestor=ancestor.f_back
            stream.write(json.dumps(row,separators=(',',':'))+'\n')
            stream.flush()
        def trace(frame,event,arg):
            if os.path.normcase(frame.f_code.co_filename) not in sources or frame.f_code.co_name not in functions:
                return None
            if event=='line':
                # Skip terminal/block iteration to avoid per-entry instrumentation.
                text=sources[os.path.normcase(frame.f_code.co_filename)][frame.f_lineno-1].strip()
                if frame.f_code.co_name=='solve' and ('block' in text or text.startswith(('for node','for i','for j','if node','i,j='))):
                    return trace
                emit(frame,event)
            elif event in ('call','return'):
                emit(frame,event)
            return trace
        sys.settrace(trace)
        try:
            e.worker(plan['prior_plan'],index)
        finally:
            sys.settrace(None)


def freeze():
    prior=e.d.read(PRIOR/'author/plan.json')
    sources=trace_sources()
    pins=dict(prior['pins'])
    for p in sources+[Path(__file__),HERE/'monitor-check.json',HERE.parent/'probe.py',
                       HERE.parent/'plan.json',HERE.parent/'run/receipt.json']:
        pins[str(p)]=e.d.digest(p)
    for p in HISTORY.glob('*/milestone-manifest.json'): pins[str(p)]=e.d.digest(p)
    for j in (2,3,4):
        assert prior['jobs'][j]['case']==1
    e.write(HERE/'plan.json',dict(name='river-lp-memory-001',
        frozen_at_utc=datetime.now(timezone.utc).isoformat(),jobs=[2,3,4],prior_plan=prior,pins=pins,
        rationale='one successful same-board baseline and two failed expansions; fixed algorithms',
        rule='trace OS memory only; no algorithm/budget changes; retain every stop; no timing ranking',
        case_timeout_seconds=180,private_limit_mib=3072))
    print('plan',e.d.digest(HERE/'plan.json'))


def check_pins():
    for p,h in plan['pins'].items(): assert e.d.digest(p)==h,p


def selftest():
    # Exact isolated-worker import spelling must exercise the original mismatch.
    from scipy.optimize import linprog
    sources={os.path.normcase(str(p.resolve())) for p in trace_sources()}
    raw={str(p.resolve()) for p in trace_sources()}
    functions={'_clean_inputs','_format_A_constraints','_linprog_highs','_highs_wrapper'}
    seen={}
    def observe(frame,event,arg):
        if event=='call' and frame.f_code.co_name in functions:
            key=frame.f_code.co_filename
            if os.path.normcase(key) in sources:
                seen[frame.f_code.co_name]=dict(file=key,original_filter_matches=key in raw)
        return None
    sys.settrace(observe)
    try:
        result=linprog([-1.],A_ub=sparse.csc_matrix([[1.]]),b_ub=[1.],
                       bounds=[(0,1)],method='highs-ds')
    finally:
        sys.settrace(None)
    assert result.success and result.x.tolist()==[1.]
    assert set(seen)==functions,seen
    assert not any(v['original_filter_matches'] for v in seen.values()),seen
    before=memory()
    allocation=bytearray(128*1024**2)
    after=memory()
    assert after['private_bytes']-before['private_bytes']>=120*1024**2
    assert after['pid']==os.getpid()
    del allocation
    matrix=sparse.csc_matrix(np.eye(3))
    buffers=visible_buffers(sys._getframe())
    assert buffers['matrix']['bytes']==matrix.data.nbytes+matrix.indices.nbytes+matrix.indptr.nbytes
    e.write(HERE/'monitor-check.json',dict(before=before,after=after,passed=True,
                                        sparse_bytes=buffers['matrix']['bytes'],trace_boundary_control=seen))


def run():
    check_pins()
    OUT.mkdir(exist_ok=False)
    e.write(OUT/'plan.json',plan)
    receipts=[]
    start=perf_counter()
    for index in plan['jobs']:
        job=plan['prior_plan']['jobs'][index]
        code=('import sys,runpy;sys.path[:0]='+repr([e.monitor.SITE,str(HERE)])+
              ';sys.argv=sys.argv[1:];runpy.run_path(sys.argv[0],run_name="__main__")')
        cmd=[e.monitor.BASE_PYTHON,'-I','-S','-B','-W','error::ResourceWarning','-c',code,
             str(HERE/'probe.py'),'worker',str(index)]
        receipt=e.monitor.monitor(cmd,plan,OUT,job['label'])
        events=[json.loads(line) for line in (OUT/(job['label']+'-trace.jsonl')).read_text().splitlines()]
        assert events and all(v['memory']['pid']==receipt['observed_pid'] for v in events)
        assert any(v['function']=='_highs_wrapper' for v in events), 'native boundary missing'
        receipt.update(label=job['label'],events=len(events),last_source=events[-1]['source_line'])
        if receipt['exit']==0:
            row=e.d.read(OUT/(job['label']+'.json'))
            old=e.d.read(PRIOR/'run'/(job['label']+'.json'))
            assert row['payoff_hashes']==old['payoff_hashes']
            assert row['probabilities']==old['probabilities']
            assert row['certificate']==old['certificate']
            assert row['solution']['realizations']==old['solution']['realizations']
            receipt['baseline_identity_verified']=True
        receipts.append(receipt)
        print(json.dumps({k:v for k,v in receipt.items() if k not in ('command',)}),flush=True)
    check_pins()
    e.write(OUT/'receipt.json',dict(seconds=perf_counter()-start,records=receipts,
        diagnostic_only=True,source_and_option_changes=False))


if __name__=='__main__':
    if sys.argv[1]=='freeze': freeze()
    elif sys.argv[1]=='selftest': selftest()
    else:
        plan=e.d.read(HERE/'plan.json')
        if sys.argv[1]=='run':
            assert e.d.digest(HERE/'plan.json')==sys.argv[2]
            run()
        else:
            check_pins()
            traced_worker(int(sys.argv[2]))
