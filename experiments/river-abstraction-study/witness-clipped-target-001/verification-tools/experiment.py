"""Fixed clipped-target learning intervention; standalone research."""
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
NEW=('clipped_target_model',)

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
    from pontius.river_witness_distillation import fit_model,predict
    # Two equal-weight cases with unequal row counts: clipped intercept=(.5+.1)/2.
    x1=np.zeros((1,11)); x2=np.zeros((3,11))
    y1=np.ones((1,4))*4; y2=np.ones((3,4))*.1
    fitted=fit_model([(x1,clip(y1),np.ones(1)),(x2,clip(y2),np.ones(3))])
    assert np.allclose(predict(fitted,x1),.3,rtol=0,atol=1e-12)
    oldfit=fit_model([(x1,y1,np.ones(1)),(x2,y2,np.ones(3))])
    assert np.allclose(clip(predict(oldfit,x1)),.5,rtol=0,atol=1e-12)
    assert np.array_equal(y1,np.ones((1,4))*4)
    print('PASS: clipping/capacity/refusals and analytic clip-before-fit versus clip-after-fit.')


def bindings(plan):
    assert sys.version_info[:3]==(3,14,6)
    assert np.__version__=='2.5.2' and scipy.__version__=='1.18.0'
    assert digest(__file__)==plan['script_sha256']
    for path,h in plan['pins'].items(): assert digest(path)==h,path

def helpers():
    spec=importlib.util.spec_from_file_location('distill',ROOT/'tools/river_witness_distillation.py')
    tool=importlib.util.module_from_spec(spec); spec.loader.exec_module(tool)
    return tool

def reconstructed(plan,tool,case,cache,split):
    original=read(Path(plan[split])/(case['id']+'.json'))
    teacher=original if split=='training' else original['teacher']
    equities=tool.old.equities_for(case,cache)
    matrix,groups,rebuilt=tool.pilot.build_inputs(case,96,equities)
    assert tool.pilot.canonical_json(rebuilt)==tool.pilot.canonical_json(teacher['inputs'])
    diagnostic=read(Path(plan['diagnostic'])/(split+'-'+case['id']+'.json'))
    assert diagnostic['case']==case
    oldmodels=read(Path(plan['evaluation'])/'models.json')['models']
    seats=[]
    for seat in (0,1):
        raw=tool.student.raw_features(matrix,equities,seat)
        assert np.array_equal(raw,diagnostic['seats'][seat]['raw'])
        opponents=[r['solution'][f'seat{seat}']['call' if seat==0 else 'bet']
                   for r in teacher['bank']['methods']]
        target=action_advantages(matrix,opponents,seat)
        assert np.array_equal(target,teacher['candidate']['proposal']['features'][seat])
        oldprediction=tool.student.predict(oldmodels[seat],raw)
        assert np.array_equal(oldprediction,diagnostic['seats'][seat]['prediction'])
        weights=matrix.joint.sum(axis=1-seat)
        seats.append(dict(raw=raw.tolist(),target=clip(target).tolist(),
            weights=weights.tolist(),old_features=clip(oldprediction).tolist()))
    return matrix,groups,dict(case=case,seats=seats)

def diagnostics(tool,seats,models):
    result=[]
    for seat,data in enumerate(seats):
        prediction=tool.student.predict(models[seat],data['raw'])
        feature=clip(prediction); target=np.asarray(data['target'])
        w=np.asarray(data['weights']); w=w/w.sum()
        metrics={}
        for name,values in (('new',feature),('old',np.asarray(data['old_features']))):
            error=values-target
            metrics[name]=dict(mse=(w@np.square(error)).tolist(),mae=(w@np.abs(error)).tolist())
        result.append(dict(**data,prediction=prediction.tolist(),features=feature.tolist(),metrics=metrics))
    return result

def fit_training(plan,tool):
    started=perf_counter(); cache={}; rows=[]
    for case in plan['training_cases']:
        _,_,row=reconstructed(plan,tool,case,cache,'training'); rows.append(row)
    loaded=perf_counter()
    models=[tool.student.fit_model([(r['seats'][seat]['raw'],r['seats'][seat]['target'],
                                    r['seats'][seat]['weights']) for r in rows]) for seat in (0,1)]
    fitted=perf_counter()
    checked=[dict(case=r['case'],seats=diagnostics(tool,r['seats'],models)) for r in rows]
    return dict(models=models,training_rows=checked,target_clip=.5,alpha=.001,
        fit_calls=2,input_reconstruction_seconds=loaded-started,fit_seconds=fitted-loaded)

def inputs(plan,tool,case,cache,models):
    matrix,oldgroups,row=reconstructed(plan,tool,case,cache,'evaluation')
    seats=diagnostics(tool,row['seats'],models)
    groups={'clipped_target_model':[]}
    for seat,data in enumerate(seats):
        k=len(set(oldgroups['uniform_equity_200'][seat]))
        labels=anchored_clusters(data['features'],matrix.joint.sum(axis=1-seat),k).tolist()
        assert len(set(labels))==k
        groups['clipped_target_model'].append(labels)
    saved=read(Path(plan['boundary'])/(case['id']+'.json'))
    assert saved['case']==case
    return matrix,groups,saved,seats

def record(case,groups,saved,solutions,seats):
    floors=dict(saved['floors'])
    floors.update({m:solutions[m]['minimum_exploitability'] for m in NEW})
    return dict(case=case,groups=groups,diagnostics=seats,solutions=solutions,floors=floors,
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
    return dict(complete=True,cases=48,board_units=8,new_lp_calls=96,overall=statistics(rows),
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
    bindings(plan); tool=helpers()
    training=fit_training(plan,tool)
    write(out/'training.json',training)  # Persist fitted models before evaluation computations.
    calls=0; original=opt.linprog
    def counted(*args,**kwargs):
        nonlocal calls
        calls+=1; assert calls<=96
        return original(*args,**kwargs)
    opt.linprog=counted
    cache={}
    for case in plan['cases']:
        matrix,groups,saved,seats=inputs(plan,tool,case,cache,training['models'])
        solutions={m:opt.solve_groups(matrix,groups[m]) for m in NEW}
        write(out/(case['id']+'.json'),record(case,groups,saved,solutions,seats))
    assert calls==96
    bindings(plan)
    write(out/'worker-complete.json',dict(complete=True,cases=48,lp_calls=calls))

def parent_verify(plan,out):
    tool=helpers()
    def forbidden(*a,**kw): raise AssertionError('parent optimizer call forbidden')
    opt.linprog=opt.solve_groups=forbidden
    training=read(out/'training.json'); rebuilt=fit_training(plan,tool)
    for key in ('models','training_rows','target_clip','alpha','fit_calls'):
        assert training[key]==rebuilt[key],key
    rows=[]; cache={}
    for case in plan['cases']:
        row=read(out/(case['id']+'.json'))
        matrix,groups,saved,seats=inputs(plan,tool,case,cache,rebuilt['models'])
        for method in NEW:opt.verify_solution(matrix,groups[method],row['solutions'][method])
        assert record(case,groups,saved,row['solutions'],seats)==row
        rows.append(row)
    bindings(plan)
    result=summary(rows)
    result['prediction_errors']={split:[{name:{metric:[sum(r[seat]['metrics'][name][metric][c]
        for r in panels)/len(panels) for c in range(4)] for metric in ('mse','mae')}
        for name in ('old','new')} for seat in (0,1)]
        for split,panels in (
            ('training',[r['seats'] for r in training['training_rows']]),
            ('evaluation',[r['diagnostics'] for r in rows]))}
    result['parent_refit_calls']=2
    write(out/'summary.json',result)

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
        assert read(out/'worker-complete.json')==dict(complete=True,cases=48,lp_calls=96)
        parent_verify(plan,out)
        write(out/'results-manifest.json',{p.name:digest(p) for p in sorted(out.iterdir()) if p.is_file()})
        write(out/'receipt.json',dict(exit=0,seconds=perf_counter()-start,
            boundary='Before worker launch through parent verification and results-manifest write; '
                     'excludes preflight, output reservation and this final receipt write.'))
    except BaseException as error:
        write(out/'failed.json',dict(error=type(error).__name__,message=str(error)))
        raise
    print(json.dumps(dict(complete=True,cases=48,new_lp_calls=96)))

if __name__=='__main__':
    if sys.argv[1]=='self-test': self_test()
    elif sys.argv[1]=='worker':
        plan=read(sys.argv[2]); worker(plan,Path(plan['output']))
    elif sys.argv[1]=='run': run(Path(sys.argv[2]))
    else: raise ValueError('unknown operation')
