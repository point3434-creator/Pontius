from hashlib import sha256
from pathlib import Path
import difflib
import json

ROOT=Path('D:/Pontius-worktrees/eval-runner-consolidation')
HERE=Path(__file__).parent
BASE=ROOT/'experiments/river-abstraction-study/witness-boundary-001'
manifest=BASE/'milestone-manifest.json'
assert sha256(manifest.read_bytes()).hexdigest()=='f66bae19b5efe17bb93623a26358d3b4e642c2af847b674a6636ca3b41997133'
source=BASE/'verification-tools/experiment.py'
assert sha256(source.read_bytes()).hexdigest()==json.loads(manifest.read_bytes())['verification-tools/experiment.py']
old=source.read_text(encoding='utf-8')
prefix=old[:old.index('def helpers():')]
prefix=prefix.replace('Fixed boundary-resolution intervention; standalone research, no model training.',
                      'Fixed clipped-target learning intervention; standalone research.')
prefix=prefix.replace("NEW=('clipped_oracle','clipped_prediction')","NEW=('clipped_target_model',)")
needle="    print('PASS: clipping endpoints/interior/signs/idempotence, arm separation, ties, refusals.')"
replacement='''    from pontius.river_witness_distillation import fit_model,predict
    # Two equal-weight cases with unequal row counts: clipped intercept=(.5+.1)/2.
    x1=np.zeros((1,11)); x2=np.zeros((3,11))
    y1=np.ones((1,4))*4; y2=np.ones((3,4))*.1
    fitted=fit_model([(x1,clip(y1),np.ones(1)),(x2,clip(y2),np.ones(3))])
    assert np.allclose(predict(fitted,x1),.3,rtol=0,atol=1e-12)
    oldfit=fit_model([(x1,y1,np.ones(1)),(x2,y2,np.ones(3))])
    assert np.allclose(clip(predict(oldfit,x1)),.5,rtol=0,atol=1e-12)
    assert np.array_equal(y1,np.ones((1,4))*4)
    print('PASS: clipping/capacity/refusals and analytic clip-before-fit versus clip-after-fit.')'''
assert needle in prefix
prefix=prefix.replace(needle,replacement)
body='''def helpers():
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

'''
aggregates=old[old.index('def average('):old.index('def worker(')].replace('new_lp_calls=192','new_lp_calls=96')
execution='''def worker(plan,out):
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

'''
tail=old[old.index('def run('):].replace('lp_calls=192','lp_calls=96')
new=prefix+body+aggregates+execution+tail
compile(new,'experiment.py','exec')
with (HERE/'experiment.py').open('x',encoding='utf-8',newline='\n') as f:f.write(new)
with (HERE/'from-boundary.diff').open('x',encoding='utf-8',newline='\n') as f:
    f.writelines(difflib.unified_diff(old.splitlines(True),new.splitlines(True),
        fromfile='sealed-boundary/experiment.py',tofile='clipped-target/experiment.py'))
print(sha256((HERE/'experiment.py').read_bytes()).hexdigest())
