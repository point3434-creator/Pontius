from datetime import datetime,timezone
from hashlib import sha256
import json
from pathlib import Path

ROOT=Path('D:/Pontius-worktrees/eval-runner-consolidation')
HERE=Path(__file__).parent
read=lambda p:json.loads(p.read_bytes())
digest=lambda p:sha256(p.read_bytes()).hexdigest()
archives={
    'evaluation':('witness-distillation-001','bc5768f4f5899b296bf7fd33eac6385021e99fffad56be47c0107608cc0bc052'),
    'old':('witness-boundary-001','f66bae19b5efe17bb93623a26358d3b4e642c2af847b674a6636ca3b41997133'),
    'new':('witness-clipped-target-001','3e4defba41f95c8926d08e0c2ee79b29de91e39047279e02cf10d01159f323cc')}
pins={};paths={}
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
for name in ('design.md','audit.py','prepare.py'):
    pins[str(HERE/name)]=digest(HERE/name)
plan=dict(schema='observed-seat-crossover-v1',
    user_words_verbatim='Can you design and run the next test?',
    recorded_at_utc=datetime.now(timezone.utc).isoformat(),**paths,
    output='D:/Pontius-training/river-abstraction-study/witness-seat-crossover-001',
    cases=prior['cases'],script_sha256=digest(HERE/'experiment.py'),pins=pins,
    new_lp_calls=0,new_model_fits=0,worker_timeout_seconds=600,
    arms=['old_old','new_old','old_new','new_new'],
    preflight_tests='Analytic crossed floors, signed effects, shared cancellation and policy refusals passed.')
assert len(plan['cases'])==48 and not Path(plan['output']).exists()
with (HERE/'plan.json').open('x',encoding='utf-8',newline='\n') as f:
    f.write(json.dumps(plan,sort_keys=True,indent=2)+'\n')
print(json.dumps(dict(plan_sha256=digest(HERE/'plan.json'),pin_count=len(pins))))
