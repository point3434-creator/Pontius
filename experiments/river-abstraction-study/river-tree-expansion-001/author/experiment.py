"""Bounded nested-tree census; preserve every failure and structurally identical cell."""
import tree as t
from tree import ROOT,OLD,d,Q,np,Path,perf_counter
import importlib.util
import json
import sys
import os
from hashlib import sha256
from datetime import datetime,timezone

HERE=Path(__file__).resolve().parent
OUT=HERE/'run'
sys.path.insert(0,str(OLD/'verification-tools'))
spec=importlib.util.spec_from_file_location('tree_monitor',OLD/'verification-tools/experiment.py')
monitor=importlib.util.module_from_spec(spec)
spec.loader.exec_module(monitor)


def write(path,value):
    with path.open('x',encoding='utf-8',newline='\n') as f:
        json.dump(value,f,indent=2,sort_keys=True,allow_nan=False)
        f.write('\n')


def freeze():
    pins=dict(d.read(OLD/'plan.json')['pins'])
    for p in HERE.iterdir():
        if p.is_file(): pins[str(p)]=d.digest(p)
    for p in d.HISTORY.glob('*/milestone-manifest.json'): pins[str(p)]=d.digest(p)
    for p in (d.HISTORY/'lp-numerical-scaling-001').glob('case-*.json'): pins[str(p)]=d.digest(p)
    jobs=[]
    cells=[]
    for j in range(4):
        record=d.read(d.b.PRIOR/f'input-{j:03d}.json')
        seen={}
        for variant in t.VARIANTS:
            nodes=t.public_tree(record,variant)
            key=json.dumps(nodes,sort_keys=True)
            label=f'{j:03d}-{variant}'
            if key in seen:
                cells.append(dict(case=j,variant=variant,label=label,alias=seen[key],
                    reason='opening bet is all-in; no legal raise response'))
                continue
            seen[key]=label
            sizes,flows=t.sequence_layout(nodes)
            jobs.append(dict(case=j,variant=variant,label=label,nodes=nodes,
                sequences=sizes,flow_rows=[len(f) for f in flows],
                terminals=sum(n['player']==-1 for n in nodes)))
            cells.append(dict(case=j,variant=variant,label=label))
    assert len(jobs)==9 and len(cells)==12
    plan=dict(name='river-tree-expansion-001',frozen_at_utc=datetime.now(timezone.utc).isoformat(),
        source_commit='6518b9d3af252c93f8a9dbdb13fb28adc2859b4c',jobs=jobs,cells=cells,pins=pins,
        hands=1081,scale=t.SCALE,behavior_grid=t.GRID,exact_gap_limit='1e-8',
        case_timeout_seconds=180,private_limit_mib=3072,max_lp_calls=18,
        lp_seconds=10,maxiter=20000,output=str(OUT),
        decision='measure strict certificate and complete cost on every distinct tree; no retries',
        python=sys.version,numpy=np.__version__,scipy=d.c.scipy.__version__)
    for p,h in pins.items(): assert d.digest(p)==h,p
    write(HERE/'plan.json',plan)
    print(json.dumps(dict(plan_sha256=d.digest(HERE/'plan.json'),
        jobs=[{k:v for k,v in j.items() if k!='nodes'} for j in jobs]),indent=2))


def bindings(plan):
    assert sys.version_info[:3]==(3,14,6)
    assert (np.__version__,d.c.scipy.__version__)==('2.5.2','1.18.0')
    assert (t.SCALE,t.GRID)==(plan['scale'],plan['behavior_grid'])
    assert all(os.environ[k]=='1' for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'))
    for p,h in plan['pins'].items(): assert d.digest(p)==h,p


def game(job):
    record=d.read(d.b.PRIOR/f"input-{job['case']:03d}.json")
    nodes=t.public_tree(record,job['variant'])
    sizes,flows=t.sequence_layout(nodes)
    assert nodes==job['nodes'] and sizes==job['sequences']
    arrays=t.payoff_arrays(record,nodes)
    hashes={str(k):sha256(v.tobytes()).hexdigest() for k,v in arrays.items()}
    return record,nodes,sizes,flows,arrays,hashes


def worker(plan,index):
    bindings(plan)
    job=plan['jobs'][index]
    start=perf_counter()
    record,nodes,sizes,flows,arrays,hashes=game(job)
    setup=perf_counter()-start
    start=perf_counter()
    solution=t.solve(nodes,sizes,flows,arrays)
    solve_seconds=perf_counter()-start
    row=dict(label=job['label'],case=job['case'],variant=job['variant'],executing_pid=os.getpid(),
        payoff_hashes=hashes,setup_seconds=setup,solve_seconds=solve_seconds,solution=solution)
    if all(x is not None for x in solution['realizations']):
        start=perf_counter()
        probs=t.behavior(nodes,solution['realizations'],1081)
        row.update(probabilities=probs,certificate=t.certificate(nodes,sizes,arrays,probs),
            certificate_seconds=perf_counter()-start)
    else:
        row['refusal']='one or both LPs returned no strategy'
    write(OUT/(job['label']+'.json'),row)
    bindings(plan)


def verify(plan,index):
    bindings(plan)
    def forbidden(*args,**kwargs): raise AssertionError('verification cannot solve')
    t.linprog=forbidden
    job=plan['jobs'][index]
    row=d.read(OUT/(job['label']+'.json'))
    record,nodes,sizes,flows,arrays,hashes=game(job)
    assert hashes==row['payoff_hashes']
    checks=t.engine_audit(record,nodes)
    baseline_overlap=None
    if 'certificate' in row:
        probs=t.behavior(nodes,row['solution']['realizations'],1081)
        assert probs==row['probabilities']
        cert=t.certificate(nodes,sizes,arrays,probs)
        assert cert==row['certificate']
        # A separate recursive rational evaluator covers nontrivial private-card subgames.
        literal=[]
        for start in (0,237,811):
            ix=[(start+17*k)%1081 for k in range(3)]
            sub={k:a[np.ix_(ix,ix)] for k,a in arrays.items()}
            sub_probs={i:[p[j] for j in ix] for i,p in probs.items()}
            value=t.literal_value(nodes,sizes,sub,sub_probs)
            assert value==Q(t.certificate(nodes,sizes,sub,sub_probs)['value'])
            literal.append(str(value))
        if job['variant']=='baseline':
            old=d.read(d.HISTORY/'lp-numerical-scaling-001'/f"case-{job['case']:03d}.json")
            lower,upper=map(Q,old['profile']['bounds'])
            baseline_overlap=max(lower,Q(cert['lower']))<=min(upper,Q(cert['upper']))
            assert baseline_overlap,'sequence-form control disagrees with old-game equilibrium bounds'
    else:
        assert not row['solution']['solver_success']
        literal=[]
    write(OUT/(job['label']+'-audit.json'),dict(passed=True,executing_pid=os.getpid(),
        label=job['label'],engine=checks,literal_subgames=literal,new_lp_calls=0,
        baseline_interval_overlap=baseline_overlap))
    bindings(plan)


def run(plan):
    bindings(plan)
    OUT.mkdir(exist_ok=False)
    write(OUT/'plan.json',plan)
    start=perf_counter()
    results=[]
    for index,job in enumerate(plan['jobs']):
        result={k:v for k,v in job.items() if k!='nodes'}
        for mode in ('worker','verify'):
            code=('import sys,runpy;sys.path[:0]='+repr([monitor.SITE,str(HERE)])+
                  ';sys.argv=sys.argv[1:];runpy.run_path(sys.argv[0],run_name="__main__")')
            cmd=[monitor.BASE_PYTHON,'-I','-S','-B','-W','error::ResourceWarning','-c',code,
                 str(HERE/'experiment.py'),mode,str(index)]
            receipt=monitor.monitor(cmd,plan,OUT,job['label']+'-'+mode)
            result[mode]=receipt
            if receipt['exit'] or receipt['stop_reason']: break
            row=d.read(OUT/(job['label']+('' if mode=='worker' else '-audit')+'.json'))
            assert row['executing_pid']==receipt['observed_pid']
            if mode=='worker':
                result['solver_success']=row['solution']['solver_success']
                result['strict_pass']=row.get('certificate',{}).get('strict_pass',False)
                result['error']=row.get('certificate',{}).get('exploitability')
                result['compute_seconds']=row['setup_seconds']+row['solve_seconds']+row.get('certificate_seconds',0)
        results.append(result)
        print(json.dumps({k:v for k,v in result.items() if k not in ('worker','verify')}),flush=True)
    bindings(plan)
    write(OUT/'receipt.json',dict(seconds=perf_counter()-start,jobs=results,cells=plan['cells'],
        all_processes_verified=all(r.get('verify',{}).get('exit')==0 for r in results),
        all_distinct_strict_pass=all(r.get('strict_pass',False) for r in results)))


if __name__=='__main__':
    if sys.argv[1]=='freeze': freeze()
    else:
        plan=d.read(HERE/'plan.json')
        if sys.argv[1]=='run':
            assert d.digest(HERE/'plan.json')==sys.argv[2]
            run(plan)
        else: globals()[sys.argv[1]](plan,int(sys.argv[2]))
