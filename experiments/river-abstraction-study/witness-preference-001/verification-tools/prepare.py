from datetime import datetime,timezone
from hashlib import sha256
import json
from pathlib import Path

ROOT=Path('D:/Pontius-worktrees/eval-runner-consolidation')
HERE=Path(__file__).parent
read=lambda p:json.loads(p.read_bytes())
digest=lambda p:sha256(p.read_bytes()).hexdigest()
archives={
    'training':('witness-pilot-001','d3b52b5f3c6046c6c36f2c967fa6d9e5e6f43608465da2cc974f94e54a121032'),
    'evaluation':('witness-distillation-001','bc5768f4f5899b296bf7fd33eac6385021e99fffad56be47c0107608cc0bc052'),
    'diagnostic':('witness-fit-diagnostic-001','bae3d425d8cb2683b5902761474dae216acc3eca503e40dbf737f60ca1046755'),
    'boundary':('witness-boundary-001','f66bae19b5efe17bb93623a26358d3b4e642c2af847b674a6636ca3b41997133'),
    'clipped':('witness-clipped-target-001','3e4defba41f95c8926d08e0c2ee79b29de91e39047279e02cf10d01159f323cc'),
    'crossover':('witness-seat-crossover-001','c2cc1f9f5cd7a5247933b3a70ad1f3ebb73e174e3506e492f33746f61fc4777b')}
paths={};pins={}
for key,(name,seal) in archives.items():
    directory=ROOT/'experiments/river-abstraction-study'/name;paths[key]=str(directory)
    manifest=directory/'milestone-manifest.json';assert digest(manifest)==seal
    pins[str(manifest)]=seal
    for name,h in read(manifest).items():
        assert digest(directory/name)==h,name
        pins[str(directory/name)]=h
prior=read(Path(paths['evaluation'])/'plan.json')
for name,h in prior['sources'].items():
    assert digest(ROOT/name)==h,name
    pins[str(ROOT/name)]=h
for name in ('design.md','audit.py','prepare.py'):pins[str(HERE/name)]=digest(HERE/name)
plan=dict(schema='observed-action-preference-v1',
    user_words_verbatim="Let's design and run a small test if you can please",
    recorded_at_utc=datetime.now(timezone.utc).isoformat(),**paths,
    output='D:/Pontius-training/river-abstraction-study/witness-preference-001',
    cases=prior['cases'],training_cases=read(Path(paths['training'])/'plan.json')['cases'],
    pins=pins,script_sha256=digest(HERE/'experiment.py'),new_lp_calls=288,
    worker_model_fits=4,parent_model_refits=4,worker_timeout_seconds=600,
    methods=['ordinary_preference','weighted_preference','exact_preference'],
    preflight='Analytic ordinary/weighted intercept fits, ties/constants, gradient and refusals passed.')
assert len(plan['cases'])==len(plan['training_cases'])==48
assert not Path(plan['output']).exists()
with (HERE/'plan.json').open('x',encoding='utf-8',newline='\n') as f:
    f.write(json.dumps(plan,sort_keys=True,indent=2)+'\n')
print(json.dumps(dict(plan_sha256=digest(HERE/'plan.json'),pins=len(pins))))
