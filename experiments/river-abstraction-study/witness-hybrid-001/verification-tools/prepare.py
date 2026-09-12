from datetime import datetime,timezone
from hashlib import sha256
import json
from pathlib import Path

ROOT=Path('D:/Pontius-worktrees/eval-runner-consolidation')
HERE=Path(__file__).parent
read=lambda p:json.loads(p.read_bytes())
digest=lambda p:sha256(p.read_bytes()).hexdigest()
archives={'training':('witness-pilot-001','d3b52b5f3c6046c6c36f2c967fa6d9e5e6f43608465da2cc974f94e54a121032'),
    'evaluation':('witness-distillation-001','bc5768f4f5899b296bf7fd33eac6385021e99fffad56be47c0107608cc0bc052'),
    'diagnostic':('witness-fit-diagnostic-001','bae3d425d8cb2683b5902761474dae216acc3eca503e40dbf737f60ca1046755')}
pins={}; paths={}
for key,(name,seal) in archives.items():
    archive=ROOT/'experiments/river-abstraction-study'/name
    paths[key]=str(archive)
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
pins[str(HERE/'design.md')]=digest(HERE/'design.md')
plan=dict(schema='observed-witness-hybrid-v1',user_words_verbatim="Let's run the next test",
    recorded_at_utc=datetime.now(timezone.utc).isoformat(),**paths,
    output='D:/Pontius-training/river-abstraction-study/witness-hybrid-001',
    cases=prior['cases'],script_sha256=digest(HERE/'experiment.py'),pins=pins,
    new_lp_calls=192,worker_timeout_seconds=600,new_model_fits=0,
    scaling='Equal block RMS within-case dispersion, computed from training only.',
    methods=['raw11','hybrid'],preflight_tests='Synthetic checks passed before plan freeze.')
assert not Path(plan['output']).exists()
with (HERE/'plan.json').open('x',encoding='utf-8',newline='\n') as f:
    f.write(json.dumps(plan,sort_keys=True,indent=2)+'\n')
print(json.dumps(dict(plan_sha256=digest(HERE/'plan.json'),pin_count=len(pins))))
