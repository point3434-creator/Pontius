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
    'boundary':('witness-boundary-001','f66bae19b5efe17bb93623a26358d3b4e642c2af847b674a6636ca3b41997133')}
pins={}; paths={}
for key,(name,seal) in archives.items():
    archive=ROOT/'experiments/river-abstraction-study'/name;paths[key]=str(archive)
    manifest=archive/'milestone-manifest.json';assert digest(manifest)==seal
    pins[str(manifest)]=seal
    for member,h in read(manifest).items():
        assert digest(archive/member)==h,member
        pins[str(archive/member)]=h
prior=read(Path(paths['evaluation'])/'plan.json')
for name,h in prior['sources'].items():
    assert digest(ROOT/name)==h,name
    pins[str(ROOT/name)]=h
for name in ('design.md','from-boundary.diff','build.py'):pins[str(HERE/name)]=digest(HERE/name)
plan=dict(schema='observed-clipped-target-learning-v1',user_words_verbatim='Please design and run the test',
    recorded_at_utc=datetime.now(timezone.utc).isoformat(),**paths,
    output='D:/Pontius-training/river-abstraction-study/witness-clipped-target-001',
    cases=prior['cases'],training_cases=read(Path(paths['training'])/'plan.json')['cases'],
    script_sha256=digest(HERE/'experiment.py'),pins=pins,clip_magnitude=.5,alpha=.001,
    new_lp_calls=96,worker_timeout_seconds=600,worker_model_fits=2,parent_verification_fits=2,
    methods=['clipped_target_model'],preflight_tests='Synthetic clipping and analytic target-fit checks passed.')
assert len(plan['cases'])==len(plan['training_cases'])==48
assert not Path(plan['output']).exists()
with (HERE/'plan.json').open('x',encoding='utf-8',newline='\n') as f:
    f.write(json.dumps(plan,sort_keys=True,indent=2)+'\n')
print(json.dumps(dict(plan_sha256=digest(HERE/'plan.json'),pin_count=len(pins))))
