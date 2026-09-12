"""One frozen classifier, sixteen new boards, no fitting or adaptive selection."""
from collections import Counter
from fractions import Fraction as Q
from hashlib import sha256
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
from time import perf_counter
import tracemalloc

ROOT=Path('D:/Pontius-worktrees/eval-runner-consolidation')
HERE=Path(__file__).parent
for key in ('OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','OMP_NUM_THREADS'):os.environ[key]='1'
SEALED=ROOT/'experiments/river-abstraction-study/witness-preference-001/verification-tools/experiment.py'
spec=importlib.util.spec_from_file_location('sealed_preference',SEALED)
pref=importlib.util.module_from_spec(spec);spec.loader.exec_module(pref)
np,scipy,opt,base=pref.np,pref.scipy,pref.opt,pref.base
read,write,digest=base.read,base.write,base.digest
METHODS=('ordinary_preference','range_response','range_equity','exact')
SEED='witness-preference-confirmation-001'

def select(excluded,pilot):
    rejected={pilot.canonical_board(b) for b in excluded}
    chosen={t:[] for t in pilot.TEXTURES};accepted=[]
    for attempt in range(10000):
        board=tuple(sorted(sorted(range(52),key=lambda c:
            (sha256(f'{SEED}|board|{attempt}|{c}'.encode()).digest(),c))[:5]))
        key=pilot.canonical_board(board);texture=pilot.texture(board)
        if key not in rejected and len(chosen[texture])<4:
            chosen[texture].append(board);rejected.add(key)
            accepted.append(dict(attempt=attempt,board=list(board),texture=texture))
        if all(len(bs)==4 for bs in chosen.values()):
            return [list(b) for t in pilot.TEXTURES for b in chosen[t]],accepted
    raise AssertionError('board selection limit')

def bindings(plan):
    assert sys.version_info[:3]==(3,14,6) and np.__version__=='2.5.2' and scipy.__version__=='1.18.0'
    assert not tracemalloc.is_tracing()
    assert digest(__file__)==plan['script_sha256']
    for p,h in plan['pins'].items():assert digest(p)==h,p
    tool=base.helpers();boards,accepted=select(plan['excluded_boards'],tool.pilot)
    assert boards==plan['boards'] and accepted==plan['selection_receipt']
    assert tool.pilot.case_grid(boards)==plan['cases']
    assert len(plan['cases'])==96 and len(boards)==16
    frozen=read(plan['candidate_path']);producer=read(Path(plan['producer'])/'training.json')
    assert frozen['models']==producer['models']['ordinary_preference']
    assert frozen['producer_training_sha256']==digest(Path(plan['producer'])/'training.json')

def self_test():
    x=np.zeros((3,78));x[:,0]=1;x[:,1]=[-1,0,1]
    coefficients=np.zeros(78);coefficients[1]=1
    model=[dict(constant=None,coefficients=coefficients.tolist())]*4
    p=pref.predict(model,x)
    assert np.allclose(p[:,0],[1/(1+np.exp(1)),.5,1/(1+np.exp(-1))],rtol=0,atol=1e-15)
    for k in (1,4,8):
        assert len(set(base.anchored_clusters(np.ones((8,4))*.5,np.ones(8),k)))==k
    v=base.difference(opt.interval(Q(1),Q(2)),opt.interval(Q(3),Q(4)))
    assert (v['lower_exact'],v['upper_exact'],v['classification'])==('-3','-1','lower')
    pilot=base.helpers().pilot
    board=[0,5,10,15,20];swapped=[4*(c//4)+(c%4+1)%4 for c in board]
    assert pilot.canonical_board(board)==pilot.canonical_board(swapped)
    print('PASS: scalar sigmoid, occupied capacity under ties, signed intervals and suit invariance.')

def inputs(plan,tool,case,cache,models):
    start=perf_counter();equities=tool.old.equities_for(case,cache)
    matrix,controls,rawinputs=tool.pilot.build_inputs(case,96,equities)
    designs=[];raw=[]
    for seat in (0,1):
        features=tool.student.raw_features(matrix,equities,seat)
        raw.append(features.tolist());designs.append(tool.student.design(features))
    prepared=perf_counter()
    features=[pref.predict(models[seat],designs[seat]) for seat in (0,1)]
    predicted=perf_counter();labels=[]
    for seat in (0,1):
        k=len(set(controls['uniform_equity_200'][seat]))
        g=base.anchored_clusters(features[seat],matrix.joint.sum(axis=1-seat),k).tolist()
        assert len(set(g))==k;labels.append(g)
    grouped=perf_counter()
    groups={m:[g.tolist() for g in controls[m]] for m in METHODS[1:]}
    groups['ordinary_preference']=labels
    assert all([len(set(g)) for g in groups[m]]==[len(set(g)) for g in labels]
               for m in ('range_response','range_equity'))
    return matrix,dict(case=case,inputs=rawinputs,raw_features=raw,
        candidate_features=[x.tolist() for x in features],groups=groups),dict(
        preparation_seconds=prepared-start,prediction_seconds=predicted-prepared,
        clustering_seconds=grouped-predicted)

def result(core,solutions):
    floors={m:solutions[m]['minimum_exploitability'] for m in METHODS}
    return dict(**core,solutions=solutions,floors=floors,
        comparisons={m:base.difference(floors['ordinary_preference'],floors[m]) for m in METHODS[1:]},
        seat_effects={m:pref.seat_delta(solutions['ordinary_preference'],solutions[m]) for m in METHODS[1:]})

def statistics(rows):
    def av(xs):return dict(**base.average(xs),counts=dict(Counter(x['classification'] for x in xs)))
    return dict(mean_floors={m:base.average([r['floors'][m] for r in rows]) for m in METHODS},
        comparisons={m:av([r['comparisons'][m] for r in rows]) for m in METHODS[1:]},
        seat_effects={m:{seat:av([r['seat_effects'][m][seat] for r in rows]) for seat in ('bettor','caller')}
                      for m in METHODS[1:]})

def summary(rows):
    assert len(rows)==96
    result=dict(cases=96,board_units=16,overall=statistics(rows),
        boards={str(b):dict(**statistics([r for r in rows if r['case']['board_index']==b]),
            pools={str(p):statistics([r for r in rows if r['case']['board_index']==b and r['case']['pool']==p])
                   for p in range(3)}) for b in range(16)},
        regimes={v:statistics([r for r in rows if r['case']['regime']==v]) for v in ('uniform','polarized')},
        textures={v:statistics([r for r in rows if r['case']['texture']==v])
                  for v in sorted({r['case']['texture'] for r in rows})},
        leave_one_board_out={str(b):statistics([r for r in rows if r['case']['board_index']!=b]) for b in range(16)})
    result['directional_replication_pass']=Q(result['overall']['comparisons']['range_response']['upper_exact'])<0
    result['sensitivity_pass']=all(Q(x['comparisons']['range_response']['upper_exact'])<0
        for panel in ('textures','leave_one_board_out') for x in result[panel].values())
    result['stage_seconds']={k:sum(r['timings'][k] for r in rows) for k in rows[0]['timings']}
    return result

def forbid_fit(tool):
    def fail(*a,**kw):raise AssertionError('model fitting forbidden in confirmation')
    pref.binary_fit=pref.training=tool.student.fit_model=tool.student.fit_models=fail

def worker(plan,out):
    bindings(plan);tool=base.helpers();forbid_fit(tool)
    models=read(plan['candidate_path'])['models'];write(out/'candidate.json',read(plan['candidate_path']))
    calls=0;original=opt.linprog
    def counted(*a,**kw):
        nonlocal calls
        calls+=1;assert calls<=768
        return original(*a,**kw)
    opt.linprog=counted;cache={}
    for case in plan['cases']:
        matrix,core,timings=inputs(plan,tool,case,cache,models)
        start=perf_counter();solutions={m:opt.solve_groups(matrix,core['groups'][m]) for m in METHODS}
        timings['solve_and_certificate_seconds']=perf_counter()-start
        write(out/(case['id']+'.json'),dict(**result(core,solutions),timings=timings))
    assert calls==768;bindings(plan)
    write(out/'worker-complete.json',dict(complete=True,cases=96,lp_calls=768,model_fits=0))

def parent_verify(plan,out):
    tool=base.helpers();forbid_fit(tool)
    def fail(*a,**kw):raise AssertionError('parent LP forbidden')
    opt.linprog=opt.solve_groups=fail
    assert read(out/'candidate.json')==read(plan['candidate_path'])
    models=read(out/'candidate.json')['models'];cache={};rows=[]
    for case in plan['cases']:
        row=read(out/(case['id']+'.json'));matrix,core,_=inputs(plan,tool,case,cache,models)
        for m in METHODS:opt.verify_solution(matrix,core['groups'][m],row['solutions'][m])
        assert result(core,row['solutions'])=={k:v for k,v in row.items() if k!='timings'}
        assert set(row['timings'])=={'preparation_seconds','prediction_seconds',
            'clustering_seconds','solve_and_certificate_seconds'}
        assert all(type(v) is float and np.isfinite(v) and v>=0 for v in row['timings'].values())
        rows.append(row)
    write(out/'summary.json',summary(rows));bindings(plan)

def run(path,expected):
    assert digest(path)==expected
    plan=read(path);bindings(plan)
    out=Path(plan['output']);out.mkdir(parents=True,exist_ok=False)
    write(out/'plan.json',plan)
    command=[sys.executable,'-B','-W','error::ResourceWarning',str(Path(__file__).resolve()),'worker',str(path),expected]
    write(out/'started.json',dict(command=command,plan_sha256=expected));start=perf_counter()
    try:
        with (out/'stdout.txt').open('xb') as stdout,(out/'stderr.txt').open('xb') as stderr:
            child=subprocess.run(command,stdout=stdout,stderr=stderr,cwd=ROOT,timeout=600)
        write(out/'worker-receipt.json',dict(exit=child.returncode,seconds=perf_counter()-start))
        assert child.returncode==0,'worker failed'
        assert read(out/'worker-complete.json')==dict(complete=True,cases=96,lp_calls=768,model_fits=0)
        parent_verify(plan,out)
        spec=importlib.util.spec_from_file_location('confirmation_audit',HERE/'audit.py')
        auditor=importlib.util.module_from_spec(spec);spec.loader.exec_module(auditor)
        write(out/'audit.json',auditor.audit(out));bindings(plan)
        write(out/'results-manifest.json',{p.name:digest(p) for p in sorted(out.iterdir()) if p.is_file()})
        write(out/'receipt.json',dict(exit=0,seconds=perf_counter()-start,
            result_manifest_sha256=digest(out/'results-manifest.json')))
        print(json.dumps(read(out/'audit.json'),indent=2))
    except BaseException as e:
        write(out/'failed.json',dict(error=type(e).__name__,message=str(e)));raise

if __name__=='__main__':
    if sys.argv[1]=='self-test':self_test()
    elif sys.argv[1]=='worker':
        assert digest(sys.argv[2])==sys.argv[3];p=read(sys.argv[2]);worker(p,Path(p['output']))
    elif sys.argv[1]=='run':run(Path(sys.argv[2]),sys.argv[3])
    else:raise ValueError('unknown operation')
