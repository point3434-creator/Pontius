from datetime import datetime,timezone
from hashlib import sha256
import json
from pathlib import Path

ROOT=Path('D:/Pontius-worktrees/eval-runner-consolidation')
HERE=Path(__file__).parent
read=lambda p:json.loads(p.read_bytes())
digest=lambda p:sha256(p.read_bytes()).hexdigest()
archives={'evaluation':('witness-distillation-001','bc5768f4f5899b296bf7fd33eac6385021e99fffad56be47c0107608cc0bc052'),
    'prior_runner':('witness-hybrid-001','ea6f2920650b3657d92183de2e7d0c5776ef3c15577b3f8e7804044bf6a54d54')}
pins={}; paths={}
for key,(name,seal) in archives.items():
    archive=ROOT/'experiments/river-abstraction-study'/name; paths[key]=str(archive)
    manifest=archive/'milestone-manifest.json'
    assert digest(manifest)==seal
    pins[str(manifest)]=seal
    for member,h in read(manifest).items():
        assert digest(archive/member)==h,member
        pins[str(archive/member)]=h
prior=read(Path(paths['evaluation'])/'plan.json')
for name,h in prior['sources'].items():
    assert digest(ROOT/name)==h,name
    pins[str(ROOT/name)]=h
for name in ('design.md','from-hybrid.diff','build.py'):
    pins[str(HERE/name)]=digest(HERE/name)
plan=dict(schema='observed-witness-boundary-v1',user_words_verbatim='Design and run the next test',
    recorded_at_utc=datetime.now(timezone.utc).isoformat(),**paths,
    output='D:/Pontius-training/river-abstraction-study/witness-boundary-001',
    cases=prior['cases'],script_sha256=digest(HERE/'experiment.py'),pins=pins,
    clip_magnitude=.5,new_lp_calls=192,worker_timeout_seconds=600,new_model_fits=0,
    methods=['clipped_oracle','clipped_prediction'],
    preflight_tests='Synthetic clipping/sign/tie/capacity/refusal checks passed before freeze.')
assert len(plan['cases'])==48 and not Path(plan['output']).exists()
with (HERE/'plan.json').open('x',encoding='utf-8',newline='\n') as f:
    f.write(json.dumps(plan,sort_keys=True,indent=2)+'\n')
print(json.dumps(dict(plan_sha256=digest(HERE/'plan.json'),pin_count=len(pins))))
