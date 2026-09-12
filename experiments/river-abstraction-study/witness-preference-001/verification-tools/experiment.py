"""Fixed action-preference classifiers and exact-feature reference."""
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
HERE=Path(__file__).parent
for key in ('OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','OMP_NUM_THREADS'):os.environ[key]='1'
BASE=ROOT/'experiments/river-abstraction-study/witness-clipped-target-001/verification-tools/experiment.py'
spec=importlib.util.spec_from_file_location('sealed_preference_base',BASE)
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
np,scipy,opt=base.np,base.scipy,base.opt
from scipy.special import expit
read,write,digest=base.read,base.write,base.digest
METHODS=('ordinary_preference','weighted_preference','exact_preference')
LEARNED=METHODS[:2]

def targets(a):
    x=np.asarray(a,float)
    assert np.isfinite(x).all()
    return np.where(x>0,1.,np.where(x<0,0.,.5))

def objective(beta,x,y,w):
    z=x@beta;penalty=.001*beta.copy();penalty[0]=0
    loss=float(w@(np.logaddexp(0,z)-y*z)+.0005*(beta[1:]@beta[1:]))
    grad=x.T@(w*(expit(z)-y))+penalty
    return loss,grad

def binary_fit(x,y,w):
    x,y,w=np.asarray(x,float),np.asarray(y,float),np.asarray(w,float)
    assert x.ndim==2 and x.shape[1]==78 and y.shape==w.shape==(len(x),)
    assert np.isfinite(x).all() and np.isfinite(y).all() and np.isfinite(w).all()
    assert (w>=0).all() and ((0<=y)&(y<=1)).all() and np.all(x[:,0]==1)
    assert w.sum()>0
    w=w/w.sum();active=y[w>0]
    if np.all(active==active[0]) and active[0] in (0.,.5,1.):
        return dict(constant=float(active[0]),coefficients=None,iterations=0,gradient_max=0.)
    beta=np.zeros(78)
    for iteration in range(81):
        loss,g=objective(beta,x,y,w);maximum=float(np.max(np.abs(g)))
        if maximum<=1e-8:
            return dict(constant=None,coefficients=beta.tolist(),iterations=iteration,
                        gradient_max=maximum,objective=loss)
        assert iteration<80,'Newton iteration limit'
        p=expit(x@beta)
        h=x.T@((w*p*(1-p))[:,None]*x)+np.diag([0.]+[.001]*77)
        direction=np.linalg.solve(h,g);descent=float(g@direction)
        assert np.isfinite(direction).all() and descent>0
        for backtrack in range(40):
            step=2.**(-backtrack);trial=beta-step*direction
            trial_loss,_=objective(trial,x,y,w)
            if trial_loss<=loss-.0001*step*descent:
                beta=trial;break
        else:raise AssertionError('Newton line search failed')
    raise AssertionError('unreachable')

def predict(model,x):
    return np.column_stack([np.full(len(x),m['constant']) if m['constant'] is not None else
                            expit(x@np.asarray(m['coefficients'])) for m in model])

def self_test():
    x=np.zeros((2,78));x[:,0]=1;y=np.array([0.,1.])
    ordinary=binary_fit(x,y,np.array([.5,.5]))
    weighted=binary_fit(x,y,np.array([.25,.75]))
    assert abs(predict([ordinary],x)[0,0]-.5)<1e-8
    assert abs(predict([weighted],x)[0,0]-.75)<1e-8
    assert binary_fit(x,np.array([.5,.5]),[1,1])['constant']==.5
    assert binary_fit(x,np.array([1.,1.]),[1,0])['constant']==1
    assert np.array_equal(targets([-3,0,2]),[0,.5,1])
    # Independent central differences include the slope penalty and weighted loss.
    x[:,1]=[-1,2];beta=np.zeros(78);beta[:2]=[.2,-.3];w=np.array([.25,.75])
    _,g=objective(beta,x,y,w)
    for j in (0,1,20):
        d=np.zeros(78);d[j]=1e-5
        numerical=(objective(beta+d,x,y,w)[0]-objective(beta-d,x,y,w)[0])/2e-5
        assert abs(numerical-g[j])<1e-8
    for bad_y,bad_w in [([0,1],[0,0]),([0,1],[-1,2]),([0,2],[1,1]),([0,float('nan')],[1,1])]:
        try:binary_fit(x,bad_y,bad_w)
        except AssertionError:pass
        else:raise AssertionError('invalid fit accepted')
    print('PASS: analytic ordinary/weighted fits, ties/constants, gradient and refusals.')

def bindings(plan):
    assert sys.version_info[:3]==(3,14,6)
    assert np.__version__=='2.5.2' and scipy.__version__=='1.18.0'
    assert digest(__file__)==plan['script_sha256']
    for path,h in plan['pins'].items():assert digest(path)==h,path

def reconstruct(plan,tool,case,cache,split):
    matrix,groups,row=base.reconstructed(plan,tool,case,cache,split)
    original=read(Path(plan[split])/(case['id']+'.json'))
    teacher=original if split=='training' else original['teacher']
    data=[]
    for seat in (0,1):
        d=row['seats'][seat];adv=np.asarray(teacher['candidate']['proposal']['features'][seat])
        assert np.array_equal(np.clip(adv,-.5,.5),d['target'])
        data.append(dict(raw=d['raw'],weights=d['weights'],advantage=adv.tolist(),
                         target=targets(adv).tolist()))
    return matrix,groups,teacher,dict(case=case,seats=data)

def training(plan,tool):
    start=perf_counter();cache={};rows=[]
    for case in plan['training_cases']:
        rows.append(reconstruct(plan,tool,case,cache,'training')[3])
    loaded=perf_counter();models={m:[] for m in LEARNED};normalizers=[]
    for seat in (0,1):
        x=np.vstack([tool.student.design(r['seats'][seat]['raw']) for r in rows])
        y=np.vstack([r['seats'][seat]['target'] for r in rows])
        advantages=np.vstack([r['seats'][seat]['advantage'] for r in rows])
        mass=np.concatenate([np.asarray(r['seats'][seat]['weights'])/
                  sum(r['seats'][seat]['weights'])/len(rows) for r in rows])
        norms=[]
        for method in LEARNED:
            columns=[]
            for c in range(4):
                w=mass if method=='ordinary_preference' else mass*np.abs(advantages[:,c])
                normalizer=float(w.sum())
                if method=='weighted_preference':norms.append(normalizer)
                columns.append(binary_fit(x,y[:,c],w) if normalizer>0 else
                    dict(constant=.5,coefficients=None,iterations=0,gradient_max=0.))
            models[method].append(columns)
        normalizers.append(norms)
    return dict(models=models,training_rows=rows,cost_normalizers=normalizers,
        model_fits=4,output_tasks=16,input_seconds=loaded-start,fit_seconds=perf_counter()-loaded)

def inputs(plan,tool,case,cache,models):
    matrix,controls,teacher,row=reconstruct(plan,tool,case,cache,'evaluation')
    groups={m:[] for m in METHODS};diagnostics=[]
    for seat,d in enumerate(row['seats']):
        x=tool.student.design(d['raw']);w=np.asarray(d['weights']);w=w/w.sum()
        a=np.asarray(d['advantage']);y=np.asarray(d['target'])
        features={m:predict(models[m][seat],x) for m in LEARNED}
        features['exact_preference']=y
        k=len(set(controls['uniform_equity_200'][seat]))
        metrics={}
        for method,v in features.items():
            assert v.shape==(96,4) and np.isfinite(v).all() and ((v>=0)&(v<=1)).all()
            labels=base.anchored_clusters(v,w,k).tolist();assert len(set(labels))==k
            groups[method].append(labels)
            # The cost of using the predicted probability as a decision against each witness.
            cost=np.abs(a)*np.where(a>0,1-v,np.where(a<0,v,0))
            metrics[method]=dict(expected_wrong_action_cost=(w@cost).tolist())
        diagnostics.append(dict(**d,features={m:v.tolist() for m,v in features.items()},metrics=metrics))
    reference=read(Path(plan['crossover'])/(case['id']+'.json'))
    assert reference['case']==case
    control=next(m['solution'] for m in teacher['bank']['methods'] if m['method']=='range_response')
    assert control['minimum_exploitability']==reference['floors']['range_response']
    return matrix,groups,reference,control,diagnostics

def seat_delta(a,b):
    ao,bo=a['seat0']['value'],b['seat0']['value']
    ac,bc=a['seat1']['value'],b['seat1']['value']
    def signed(lo,hi):return dict(**opt.interval(lo,hi),classification=
        'lower' if hi<0 else 'higher' if lo>0 else 'overlapping')
    return dict(bettor=signed((Q(bo['lower_exact'])-Q(ao['upper_exact']))/2,
                              (Q(bo['upper_exact'])-Q(ao['lower_exact']))/2),
        caller=signed((Q(ac['lower_exact'])-Q(bc['upper_exact']))/2,
                      (Q(ac['upper_exact'])-Q(bc['lower_exact']))/2))

def record(case,groups,reference,control,diagnostics,solutions):
    floors=dict(reference['floors']);floors.update({m:solutions[m]['minimum_exploitability'] for m in METHODS})
    return dict(case=case,groups=groups,diagnostics=diagnostics,solutions=solutions,floors=floors,
        comparisons={m:{other:base.difference(floors[m],v) for other,v in floors.items() if m!=other}
                     for m in METHODS},
        seat_effects={**{m:seat_delta(solutions[m],control) for m in METHODS},
                     'weighted_minus_ordinary':seat_delta(solutions['weighted_preference'],solutions['ordinary_preference'])})

def stats(rows):
    def avg(xs):return dict(**base.average(xs),counts=dict(Counter(x['classification'] for x in xs)))
    return dict(mean_floors={m:base.average([r['floors'][m] for r in rows]) for m in rows[0]['floors']},
        comparisons={m:{other:avg([r['comparisons'][m][other] for r in rows])
                         for other in rows[0]['comparisons'][m]} for m in METHODS},
        seat_effects={m:{seat:avg([r['seat_effects'][m][seat] for r in rows]) for seat in ('bettor','caller')}
                      for m in rows[0]['seat_effects']})

def summarize(rows):
    assert len(rows)==48
    return dict(cases=48,overall=stats(rows),
        boards={str(b):dict(**stats([r for r in rows if r['case']['board_index']==b]),
            pools={str(p):stats([r for r in rows if r['case']['board_index']==b and r['case']['pool']==p])
                   for p in range(3)}) for b in range(8)},
        regimes={v:stats([r for r in rows if r['case']['regime']==v]) for v in ('uniform','polarized')},
        textures={v:stats([r for r in rows if r['case']['texture']==v])
                  for v in sorted({r['case']['texture'] for r in rows})},
        leave_one_board_out={str(b):stats([r for r in rows if r['case']['board_index']!=b]) for b in range(8)})

def worker(plan,out):
    bindings(plan);tool=base.helpers();fitted=training(plan,tool)
    write(out/'training.json',fitted)
    calls=0;original=opt.linprog
    def counted(*args,**kwargs):
        nonlocal calls
        calls+=1;assert calls<=288
        return original(*args,**kwargs)
    opt.linprog=counted;cache={}
    for case in plan['cases']:
        matrix,groups,reference,control,diagnostics=inputs(plan,tool,case,cache,fitted['models'])
        solutions={m:opt.solve_groups(matrix,groups[m]) for m in METHODS}
        write(out/(case['id']+'.json'),record(case,groups,reference,control,diagnostics,solutions))
    assert calls==288;bindings(plan)
    write(out/'worker-complete.json',dict(complete=True,cases=48,lp_calls=288,model_fits=4))

def verify(plan,out):
    tool=base.helpers()
    def forbidden(*a,**kw):raise AssertionError('parent LP call forbidden')
    opt.linprog=opt.solve_groups=forbidden
    saved=read(out/'training.json');rebuilt=training(plan,tool)
    for key in ('models','training_rows','cost_normalizers','model_fits','output_tasks'):
        assert saved[key]==rebuilt[key],key
    cache={};rows=[]
    for case in plan['cases']:
        row=read(out/(case['id']+'.json'))
        matrix,groups,reference,control,diagnostics=inputs(plan,tool,case,cache,rebuilt['models'])
        for m in METHODS:opt.verify_solution(matrix,groups[m],row['solutions'][m])
        assert record(case,groups,reference,control,diagnostics,row['solutions'])==row
        rows.append(row)
    result=summarize(rows);result['parent_model_refits']=4
    write(out/'summary.json',result);bindings(plan)

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
        assert read(out/'worker-complete.json')==dict(complete=True,cases=48,lp_calls=288,model_fits=4)
        verify(plan,out)
        spec=importlib.util.spec_from_file_location('preference_audit',HERE/'audit.py')
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
        assert digest(sys.argv[2])==sys.argv[3];plan=read(sys.argv[2]);worker(plan,Path(plan['output']))
    elif sys.argv[1]=='run':run(Path(sys.argv[2]),sys.argv[3])
    else:raise ValueError('unknown operation')
