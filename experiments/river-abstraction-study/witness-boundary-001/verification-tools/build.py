"""Adapt the sealed standalone experiment via a retained, bounded source diff."""
from pathlib import Path
from hashlib import sha256
import difflib
import json

ROOT=Path('D:/Pontius-worktrees/eval-runner-consolidation')
HERE=Path(__file__).parent
ARCHIVE=ROOT/'experiments/river-abstraction-study/witness-hybrid-001'
manifest=ARCHIVE/'milestone-manifest.json'
assert sha256(manifest.read_bytes()).hexdigest()=='ea6f2920650b3657d92183de2e7d0c5776ef3c15577b3f8e7804044bf6a54d54'
source=ARCHIVE/'verification-tools/experiment.py'
assert sha256(source.read_bytes()).hexdigest()==json.loads(manifest.read_bytes())['verification-tools/experiment.py']
old=source.read_text(encoding='utf-8')
new=old.replace('Fixed combined-feature intervention','Fixed boundary-resolution intervention')
new=new.replace("NEW=('raw11','hybrid')","NEW=('clipped_oracle','clipped_prediction')")
new=new.replace('from pontius.river_witness_groups import difference',
                'from pontius.river_witness_groups import difference, action_advantages')
start=new.index('def scale('); end=new.index('def bindings(')
new=new[:start]+'''def clip(features):
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


'''+new[end:]
start=new.index('def scales_for('); end=new.index('def record(')
new=new[:start]+'''def transform_config(plan):
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


'''+new[end:]
new=new.replace('def record(case,groups,saved,solutions):','def record(case,groups,saved,solutions,feature_rows):')
new=new.replace('return dict(case=case,groups=groups,solutions=solutions,floors=floors,',
                'return dict(case=case,groups=groups,features=feature_rows,solutions=solutions,floors=floors,')
new=new.replace('scales=scales_for(plan)','config=transform_config(plan)')
new=new.replace("write(out/'scales.json',scales)","write(out/'transform.json',config)")
new=new.replace("assert scales==read(out/'scales.json')","assert config==read(out/'transform.json')")
new=new.replace('matrix,groups,saved=inputs(plan,tool,case,cache,scales)',
                'matrix,groups,saved,feature_rows=inputs(plan,tool,case,cache,config)')
new=new.replace('record(case,groups,saved,solutions)','record(case,groups,saved,solutions,feature_rows)')
new=new.replace("record(case,groups,saved,row['solutions'])","record(case,groups,saved,row['solutions'],feature_rows)")
assert 'scales' not in new and 'raw11' not in new and 'hybrid' not in new
compile(new,'experiment.py','exec')
with (HERE/'experiment.py').open('x',encoding='utf-8',newline='\n') as f:f.write(new)
with (HERE/'from-hybrid.diff').open('x',encoding='utf-8',newline='\n') as f:
    f.writelines(difflib.unified_diff(old.splitlines(True),new.splitlines(True),
                 fromfile='sealed-hybrid/experiment.py',tofile='boundary/experiment.py'))
print(sha256((HERE/'experiment.py').read_bytes()).hexdigest())
