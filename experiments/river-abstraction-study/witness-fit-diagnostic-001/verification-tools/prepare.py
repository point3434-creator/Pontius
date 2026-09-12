from datetime import datetime,timezone
from hashlib import sha256
import json
from pathlib import Path

ROOT=Path('D:/Pontius-worktrees/eval-runner-consolidation')
HERE=Path(__file__).parent
read=lambda p:json.loads(p.read_bytes())
digest=lambda p:sha256(p.read_bytes()).hexdigest()
training=ROOT/'experiments/river-abstraction-study/witness-pilot-001'
evaluation=ROOT/'experiments/river-abstraction-study/witness-distillation-001'
expected={training:'d3b52b5f3c6046c6c36f2c967fa6d9e5e6f43608465da2cc974f94e54a121032',
          evaluation:'bc5768f4f5899b296bf7fd33eac6385021e99fffad56be47c0107608cc0bc052'}
pins={}
for archive,seal in expected.items():
    manifest=archive/'milestone-manifest.json'
    assert digest(manifest)==seal
    pins[str(manifest)]=seal
    for name,h in read(manifest).items():
        assert digest(archive/name)==h,name
        pins[str(archive/name)]=h
for name,h in read(evaluation/'plan.json')['sources'].items():
    assert digest(ROOT/name)==h,name
    pins[str(ROOT/name)]=h
pins[str(HERE/'design.md')]=digest(HERE/'design.md')
plan=dict(schema='frozen-witness-fit-diagnostic-v1',
    user_words_verbatim="Let's design and run the next test",
    recorded_at_utc=datetime.now(timezone.utc).isoformat(),
    training=str(training),evaluation=str(evaluation),
    output='D:/Pontius-training/river-abstraction-study/witness-fit-diagnostic-001',
    script_sha256=digest(HERE/'diagnose.py'),pins=pins,
    worker_timeout_seconds=300,new_fits=0,new_lp_calls=0,cases=96,
    test_receipt='Analytic synthetic checks exited 0 before plan creation; Python 3.14.6.',
    design_sha256=digest(HERE/'design.md'))
assert not Path(plan['output']).exists()
with (HERE/'plan.json').open('x',encoding='utf-8',newline='\n') as f:
    f.write(json.dumps(plan,sort_keys=True,indent=2)+'\n')
print(json.dumps(dict(plan_sha256=digest(HERE/'plan.json'),pin_count=len(pins))))
