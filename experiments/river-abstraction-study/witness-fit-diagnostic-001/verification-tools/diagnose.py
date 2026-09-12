"""Frozen-model diagnostic on two observed panels; no model fits or solver calls."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
from hashlib import sha256
from time import perf_counter

ROOT = Path('D:/Pontius-worktrees/eval-runner-consolidation')
for key in ('OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','OMP_NUM_THREADS'):
    os.environ[key] = '1'
sys.path.insert(0,str(ROOT/'src'))
import numpy as np
import scipy

read = lambda p: json.loads(Path(p).read_bytes())
digest = lambda p: sha256(Path(p).read_bytes()).hexdigest()

def write(path,value):
    with Path(path).open('x',encoding='utf-8',newline='\n') as f:
        f.write(json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n')

def metrics(y,p,w,constant):
    y,p,w = (np.asarray(v,dtype=float) for v in (y,p,w))
    assert y.ndim == 1 and y.shape == p.shape == w.shape and len(y)
    assert np.isfinite(y).all() and np.isfinite(p).all() and np.isfinite(w).all()
    assert (w>=0).all() and w.sum()>0 and np.isfinite(constant)
    w = w/w.sum()
    error = p-y
    mse = float(w@np.square(error))
    baseline = float(w@np.square(y-constant))
    ym,pm = float(w@y),float(w@p)
    yvar,pvar = float(w@np.square(y-ym)),float(w@np.square(p-pm))
    active = np.abs(y)>1e-10
    mismatch = ((y>0)!=(p>0)) & active
    loss = np.maximum(y,0)-y*(p>0)
    result = dict(mse=mse,mae=float(w@np.abs(error)),bias=float(w@error),
        baseline_mse=baseline,skill_vs_training_mean=1-mse/baseline if baseline>0 else None,
        target_mean=ym,prediction_mean=pm,target_sd=float(np.sqrt(yvar)),
        prediction_sd=float(np.sqrt(pvar)),correlation=float(w@((y-ym)*(p-pm)) /
            np.sqrt(yvar*pvar)) if yvar*pvar>0 else None,
        active_mass=float(w@active),sign_mismatch_active=float(w@mismatch/(w@active))
            if w@active>0 else None,opportunity_cost=float(w@loss))
    bands = {}
    for name,mask in [('near_0_to_0.1',np.abs(y)<=.1),
                      ('middle_0.1_to_0.5',(np.abs(y)>.1)&(np.abs(y)<=.5)),
                      ('far_over_0.5',np.abs(y)>.5)]:
        mass = float(w@mask)
        active_mass = float(w@(mask&active))
        bands[name] = dict(mass=mass,mse=float(w@(np.square(error)*mask)/mass) if mass else None,
            opportunity_cost=float(w@(loss*mask)/mass) if mass else None,
            active_mass=active_mass,sign_mismatch_active=float(w@(mismatch&mask)/active_mass)
                if active_mass else None)
    result['bands'] = bands
    return result

def self_test():
    r = metrics([-2,0,2],[1,-1,-1],[1,2,1],0)
    assert r['mse'] == 5 and r['mae'] == 2 and r['bias'] == -.5
    assert r['baseline_mse'] == 2 and r['opportunity_cost'] == 1
    assert r['active_mass'] == .5 and r['sign_mismatch_active'] == 1
    assert r['bands']['near_0_to_0.1']['mass'] == .5
    assert r['bands']['far_over_0.5']['mse'] == 9
    assert r['bands']['middle_0.1_to_0.5']['mse'] is None
    perfect = metrics([-.1,.1,.5,-.5,1],[-.1,.1,.5,-.5,1],[1]*5,0)
    assert perfect['mse'] == perfect['opportunity_cost'] == 0
    assert perfect['bands']['near_0_to_0.1']['mass'] == .4
    assert perfect['bands']['middle_0.1_to_0.5']['mass'] == .4
    assert perfect['bands']['far_over_0.5']['mass'] == .2
    assert metrics([1,-1],[0,0],[1,1],0)['opportunity_cost'] == .5
    assert metrics([0],[0],[1],0)['skill_vs_training_mean'] is None
    assert metrics([0],[0],[1],0)['sign_mismatch_active'] is None
    for bad in ([0,0],[-1,2]):
        try: metrics([1,2],[1,2],bad,0)
        except AssertionError: pass
        else: raise AssertionError('invalid weights accepted')
    print('Analytic metric checks passed: weights, signs, ties, bands, undefined metrics, refusals.')

def verify(plan):
    assert sys.version_info[:3] == (3,14,6)
    assert np.__version__ == '2.5.2' and scipy.__version__ == '1.18.0'
    assert digest(__file__) == plan['script_sha256']
    for path,h in plan['pins'].items():
        assert digest(path) == h,path

def summarize(rows,constants):
    result = []
    for seat in (0,1):
        values = [r['seats'][seat] for r in rows]
        y = np.vstack([r['target'] for r in values])
        p = np.vstack([r['prediction'] for r in values])
        w = np.concatenate([np.asarray(r['weights'])/len(rows) for r in values])
        result.append([metrics(y[:,c],p[:,c],w,constants[seat][c]) for c in range(4)])
    return result

def worker(plan,out):
    verify(plan)
    spec = importlib.util.spec_from_file_location('frozen_tool',ROOT/'tools/river_witness_distillation.py')
    tool = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tool)
    import pontius.river_group_optimality as opt
    import scipy.optimize
    def forbidden(*args,**kwargs):
        raise AssertionError('fitting or optimization forbidden in this diagnostic')
    opt.linprog = scipy.optimize.linprog = forbidden
    opt.solve_seat = opt.solve_groups = tool.student.solve_groups = tool.pilot.solve_groups = forbidden
    tool.student.fit_model = tool.student.fit_models = np.linalg.solve = forbidden
    archive = Path(plan['evaluation'])
    trained = read(archive/'models.json')
    models = trained['models']
    all_rows = {}
    for split in ('training','evaluation'):
        directory = Path(plan[split])
        cases = read(directory/'plan.json')['cases']
        assert len(cases)==48 and len({c['board_index'] for c in cases})==8
        cache,rows = {},[]
        for case in cases:
            saved = read(directory/(case['id']+'.json'))
            teacher = saved if split=='training' else saved['teacher']
            equities = tool.old.equities_for(case,cache)
            matrix,_,inputs = tool.pilot.build_inputs(case,96,equities)
            assert tool.pilot.canonical_json(inputs)==tool.pilot.canonical_json(teacher['inputs'])
            seats=[]
            for seat in (0,1):
                raw = tool.student.raw_features(matrix,equities,seat)
                prediction = tool.student.predict(models[seat],raw)
                target = np.asarray(teacher['candidate']['proposal']['features'][seat])
                weights = matrix.joint.sum(axis=1-seat)
                weights = weights/weights.sum()
                assert np.allclose(weights,teacher['candidate']['proposal']['marginals'][seat],
                                   rtol=0,atol=1e-14)
                if split=='evaluation':
                    assert np.array_equal(prediction,saved['student']['proposal']['features'][seat])
                seats.append(dict(raw=raw.tolist(),prediction=prediction.tolist(),target=target.tolist(),
                                  weights=weights.tolist()))
            row=dict(split=split,case=case,seats=seats)
            write(out/(split+'-'+case['id']+'.json'),row)
            rows.append(row)
        all_rows[split]=rows
        print(split+': 48 cases reconstructed',flush=True)
    constants = []
    for seat in (0,1):
        means = [np.asarray(r['seats'][seat]['weights'])@np.asarray(r['seats'][seat]['target'])
                 for r in all_rows['training']]
        constants.append(np.mean(means,axis=0).tolist())
    summary = dict(complete=True,training_mean_constants=constants,panels={})
    for split,rows in all_rows.items():
        summary['panels'][split]=dict(overall=summarize(rows,constants),
            boards={str(b):summarize([r for r in rows if r['case']['board_index']==b],constants)
                    for b in range(8)},
            regimes={regime:summarize([r for r in rows if r['case']['regime']==regime],constants)
                     for regime in ('uniform','polarized')})
    verify(plan)
    write(out/'summary.json',summary)
    write(out/'results-manifest.json',{p.name:digest(p) for p in sorted(out.iterdir())
        if p.is_file() and (p.name.startswith(('training-','evaluation-')) or p.name=='summary.json')})

def run(path):
    plan = read(path)
    verify(plan)
    out = Path(plan['output'])
    out.mkdir(parents=True,exist_ok=False)
    write(out/'plan.json',plan)
    command=[sys.executable,'-B',str(Path(__file__).resolve()),'worker',str(path)]
    write(out/'started.json',dict(command=command,plan_sha256=digest(path)))
    try:
        with (out/'stdout.txt').open('xb') as stdout,(out/'stderr.txt').open('xb') as stderr:
            start=perf_counter()
            child=subprocess.run(command,stdout=stdout,stderr=stderr,timeout=300,cwd=ROOT)
            elapsed=perf_counter()-start
        write(out/'receipt.json',dict(exit=child.returncode,worker_process_seconds=elapsed,
            boundary='Immediately before child execution through exit; excludes parent checks.'))
        assert child.returncode==0,'worker failed'
        entries=read(out/'results-manifest.json')
        assert len(entries)==97
        for name,h in entries.items(): assert digest(out/name)==h,name
        assert read(out/'summary.json')['complete'] is True
        verify(plan)
    except BaseException as error:
        write(out/'failed.json',dict(error=type(error).__name__,message=str(error)))
        raise
    print(json.dumps(dict(complete=True,cases=96,worker_seconds=elapsed)))

if __name__=='__main__':
    if sys.argv[1]=='self-test': self_test()
    elif sys.argv[1]=='worker':
        plan=read(sys.argv[2])
        worker(plan,Path(plan['output']))
    elif sys.argv[1]=='run': run(Path(sys.argv[2]))
    else: raise ValueError('unknown operation')
