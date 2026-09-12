"""Fixed boundary-resolution intervention; standalone research, no model training."""
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

ROOT=Path('D:/Pontius-worktrees/eval-runner-consolidation')
for key in ('OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','OMP_NUM_THREADS'):
    os.environ[key]='1'
sys.path.insert(0,str(ROOT/'src'))
import numpy as np
import scipy
from pontius.river_abstraction_study import anchored_clusters
from pontius.river_witness_groups import difference, action_advantages
import pontius.river_group_optimality as opt

read=lambda p:json.loads(Path(p).read_bytes())
digest=lambda p:sha256(Path(p).read_bytes()).hexdigest()
NEW=('clipped_oracle','clipped_prediction')

def write(path,value):
    with Path(path).open('x',encoding='utf-8',newline='\n') as f:
        f.write(json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n')

def clip(features):
    x=np.asarray(features,float)
    assert x.ndim==2 and x.shape[1]==4 and len(x)>0 and np.isfinite(x).all()
    return np.clip(x,-.5,.5)

def self_test():
    x=np.array([[-2,-.5,-.1,0],[.1,.5,2,4.]])
    expected=np.array([[-.5,-.5,-.1,0],[.1,.5,.5,.5]])
    assert np.array_equal(clip(x),expected)
    assert np.array_equal(np.sign(clip(x)),np.sign(x))
    assert np.array_equal(clip(clip(x)),clip(x))
    assert np.array_equal(clip(x)[np.abs(x)<=.5],x[np.abs(x)<=.5])
    # Independent arms share a transform but cannot overwrite or consume each other.
    prediction=np.ones((2,4))*-.2
    before=prediction.copy(); oracle=clip(x)
    assert np.array_equal(clip(prediction),before) and np.array_equal(prediction,before)
    assert not np.array_equal(oracle,clip(prediction))
    tied=clip(np.ones((7,4))*10)
    for k in range(1,8): assert len(set(anchored_clusters(tied,np.ones(7),k)))==k
    for bad in (np.array([[0,1]]),np.array([[0,0,0,float('nan')]]),
                np.array([[0,0,0,float('inf')]]),np.empty((0,4))):
        try: clip(bad)
        except AssertionError: pass
        else: raise AssertionError('invalid features accepted')
    print('PASS: clipping endpoints/interior/signs/idempotence, arm separation, ties, refusals.')


def bindings(plan):
    assert sys.version_info[:3]==(3,14,6)
    assert np.__version__=='2.5.2' and scipy.__version__=='1.18.0'
    assert digest(__file__)==plan['script_sha256']
    for path,h in plan['pins'].items(): assert digest(path)==h,path

def helpers():
    spec=importlib.util.spec_from_file_location('distill',ROOT/'tools/river_witness_distillation.py')
    tool=importlib.util.module_from_spec(spec); spec.loader.exec_module(tool)
    def nofit(*a,**kw): raise AssertionError('model fitting forbidden')
    tool.student.fit_model=tool.student.fit_models=np.linalg.solve=nofit
    return tool

def transform_config(plan):
    assert plan['clip_magnitude']==.5
    return dict(clip_magnitude=.5)

def inputs(plan,tool,case,cache,config):
    assert config==dict(clip_magnitude=.5)
    saved=read(Path(plan['evaluation'])/(case['id']+'.json'))
    assert saved['case']==case
    equities=tool.old.equities_for(case,cache)
    matrix,oldgroups,rebuilt=tool.pilot.build_inputs(case,96,equities)
    assert tool.pilot.canonical_json(rebuilt)==tool.pilot.canonical_json(saved['teacher']['inputs'])
    groups={method:[] for method in NEW}; feature_rows={method:[] for method in NEW}
    models=read(Path(plan['evaluation'])/'models.json')['models']
    for seat in (0,1):
        raw=tool.student.raw_features(matrix,equities,seat)
        prediction=tool.student.predict(models[seat],raw)
        assert np.array_equal(prediction,saved['student']['proposal']['features'][seat])
        opponents=[r['solution'][f'seat{seat}']['call' if seat==0 else 'bet']
                   for r in saved['teacher']['bank']['methods']]
        oracle=action_advantages(matrix,opponents,seat)
        assert np.array_equal(oracle,saved['teacher']['candidate']['proposal']['features'][seat])
        transformed=dict(clipped_oracle=clip(oracle),clipped_prediction=clip(prediction))
        weights=matrix.joint.sum(axis=1-seat)
        k=len(set(oldgroups['uniform_equity_200'][seat]))
        for method in NEW:
            labels=anchored_clusters(transformed[method],weights,k).tolist()
            assert len(set(labels))==k
            groups[method].append(labels)
            feature_rows[method].append(transformed[method].tolist())
    return matrix,groups,saved,feature_rows


def record(case,groups,saved,solutions,feature_rows):
    floors={c['method']:c['solution']['minimum_exploitability']
            for c in saved['teacher']['bank']['methods']}
    floors['direct_witness']=saved['teacher']['candidate']['solution']['minimum_exploitability']
    floors['predicted_only']=saved['student']['solution']['minimum_exploitability']
    floors.update({m:solutions[m]['minimum_exploitability'] for m in NEW})
    return dict(case=case,groups=groups,features=feature_rows,solutions=solutions,floors=floors,
        comparisons={m:{other:difference(floors[m],value) for other,value in floors.items()
                         if other!=m} for m in NEW})

def average(intervals):
    lo=sum(Q(i['lower_exact']) for i in intervals)/len(intervals)
    hi=sum(Q(i['upper_exact']) for i in intervals)/len(intervals)
    return opt.interval(lo,hi)

def statistics(rows):
    return dict(mean_floors={m:average([r['floors'][m] for r in rows]) for m in rows[0]['floors']},
        comparisons={m:{other:dict(**average([r['comparisons'][m][other] for r in rows]),
            counts=dict(Counter(r['comparisons'][m][other]['classification'] for r in rows)))
            for other in rows[0]['comparisons'][m]} for m in NEW})

def summary(rows):
    assert len(rows)==48
    return dict(complete=True,cases=48,board_units=8,new_lp_calls=192,overall=statistics(rows),
        boards={str(b):dict(**statistics([r for r in rows if r['case']['board_index']==b]),
            pools={str(p):statistics([r for r in rows if r['case']['board_index']==b and
                                     r['case']['pool']==p]) for p in range(3)}) for b in range(8)},
        regimes={regime:statistics([r for r in rows if r['case']['regime']==regime])
                 for regime in ('uniform','polarized')},
        textures={t:statistics([r for r in rows if r['case']['texture']==t])
                  for t in sorted({r['case']['texture'] for r in rows})},
        leave_one_board_out={str(b):statistics([r for r in rows if r['case']['board_index']!=b])
                             for b in range(8)})

def worker(plan,out):
    bindings(plan); tool=helpers(); config=transform_config(plan)
    write(out/'transform.json',config)
    calls=0; original=opt.linprog
    def counted(*args,**kwargs):
        nonlocal calls
        calls+=1
        assert calls<=192
        return original(*args,**kwargs)
    opt.linprog=counted
    cache={}
    for case in plan['cases']:
        matrix,groups,saved,feature_rows=inputs(plan,tool,case,cache,config)
        solutions={m:opt.solve_groups(matrix,groups[m]) for m in NEW}
        write(out/(case['id']+'.json'),record(case,groups,saved,solutions,feature_rows))
    assert calls==192
    bindings(plan)
    write(out/'worker-complete.json',dict(complete=True,cases=48,lp_calls=calls))

def parent_verify(plan,out):
    tool=helpers()
    def forbidden(*a,**kw): raise AssertionError('parent optimizer call forbidden')
    opt.linprog=opt.solve_groups=forbidden
    config=transform_config(plan)
    assert config==read(out/'transform.json')
    rows=[]; cache={}
    for case in plan['cases']:
        row=read(out/(case['id']+'.json'))
        matrix,groups,saved,feature_rows=inputs(plan,tool,case,cache,config)
        for method in NEW:
            opt.verify_solution(matrix,groups[method],row['solutions'][method])
        assert record(case,groups,saved,row['solutions'],feature_rows)==row
        rows.append(row)
    bindings(plan)
    write(out/'summary.json',summary(rows))

def run(path):
    plan=read(path); bindings(plan)
    out=Path(plan['output']); out.mkdir(parents=True,exist_ok=False)
    write(out/'plan.json',plan)
    command=[sys.executable,'-B',str(Path(__file__).resolve()),'worker',str(path)]
    write(out/'started.json',dict(command=command,plan_sha256=digest(path)))
    start=perf_counter()
    try:
        with (out/'stdout.txt').open('xb') as stdout,(out/'stderr.txt').open('xb') as stderr:
            child=subprocess.run(command,stdout=stdout,stderr=stderr,cwd=ROOT,timeout=600)
        write(out/'worker-receipt.json',dict(exit=child.returncode,seconds=perf_counter()-start))
        assert child.returncode==0,'worker failed'
        assert read(out/'worker-complete.json')==dict(complete=True,cases=48,lp_calls=192)
        parent_verify(plan,out)
        write(out/'results-manifest.json',{p.name:digest(p) for p in sorted(out.iterdir()) if p.is_file()})
        write(out/'receipt.json',dict(exit=0,seconds=perf_counter()-start,
            boundary='Before worker launch through parent verification and results-manifest write; '
                     'excludes preflight, output reservation and this final receipt write.'))
    except BaseException as error:
        write(out/'failed.json',dict(error=type(error).__name__,message=str(error)))
        raise
    print(json.dumps(dict(complete=True,cases=48,new_lp_calls=192)))

if __name__=='__main__':
    if sys.argv[1]=='self-test': self_test()
    elif sys.argv[1]=='worker':
        plan=read(sys.argv[2]); worker(plan,Path(plan['output']))
    elif sys.argv[1]=='run': run(Path(sys.argv[2]))
    else: raise ValueError('unknown operation')
