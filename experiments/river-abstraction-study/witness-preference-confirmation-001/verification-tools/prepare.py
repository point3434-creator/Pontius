from datetime import datetime,timezone
from hashlib import sha256
import importlib.util
import json
from pathlib import Path

ROOT=Path('D:/Pontius-worktrees/eval-runner-consolidation')
HERE=Path(__file__).parent
PRODUCER=ROOT/'experiments/river-abstraction-study/witness-preference-001'
SEAL='15de2891f758824d1a7db69117f4bfbb6b6e893b0fe87ad86a1e409d304636c4'
read=lambda p:json.loads(p.read_bytes())
digest=lambda p:sha256(p.read_bytes()).hexdigest()

def write(path,value):
    with path.open('x',encoding='utf-8',newline='\n') as f:
        f.write(json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n')

assert digest(PRODUCER/'milestone-manifest.json')==SEAL
pins={str(PRODUCER/'milestone-manifest.json'):SEAL}
for name,h in read(PRODUCER/'milestone-manifest.json').items():
    assert digest(PRODUCER/name)==h,name
    pins[str(PRODUCER/name)]=h
old=read(PRODUCER/'plan.json')
for path,h in old['pins'].items():
    assert digest(Path(path))==h,path
    pins[path]=h
fitted=read(PRODUCER/'training.json')
candidate=dict(schema='frozen-ordinary-preference-v1',producer_manifest_sha256=SEAL,
    producer_training_sha256=digest(PRODUCER/'training.json'),
    models=fitted['models']['ordinary_preference'],features='unchanged eleven raw probability features',
    basis='unchanged 78-column quadratic',outputs='four sigmoid preferences per seat',
    grouping='unchanged anchored_clusters with matched occupied capacity',model_fits=0)
write(HERE/'candidate.json',candidate)  # Freeze model before selecting the new panel.
spec=importlib.util.spec_from_file_location('confirmation',HERE/'experiment.py')
exp=importlib.util.module_from_spec(spec);spec.loader.exec_module(exp)
tool=exp.base.helpers()
from pontius.river_abstraction_study import DEVELOPMENT_BOARDS,HOLDOUT_BOARDS
excluded=sorted(set(tuple(b) for b in (*DEVELOPMENT_BOARDS,*HOLDOUT_BOARDS,
    *[c['board'] for c in old['training_cases']],*[c['board'] for c in old['cases']])))
assert len(excluded)==20
boards,receipt=exp.select(excluded,tool.pilot)
assert len({tool.pilot.canonical_board(b) for b in boards})==16
assert not ({tool.pilot.canonical_board(b) for b in boards}&{tool.pilot.canonical_board(b) for b in excluded})
for name in ('design.md','candidate.json','audit.py','prepare.py'):
    pins[str(HERE/name)]=digest(HERE/name)
plan=dict(schema='fresh-ordinary-preference-confirmation-v1',
    user_words_verbatim='Freeze design and run next text',
    recorded_at_utc=datetime.now(timezone.utc).isoformat(),producer=str(PRODUCER),
    candidate_path=str(HERE/'candidate.json'),candidate_sha256=digest(HERE/'candidate.json'),
    selection_seed=exp.SEED,excluded_boards=[list(b) for b in excluded],boards=boards,
    selection_receipt=receipt,cases=tool.pilot.case_grid(boards),
    output='D:/Pontius-training/river-abstraction-study/witness-preference-confirmation-001',
    script_sha256=digest(HERE/'experiment.py'),pins=pins,model_fits=0,new_lp_calls=768,
    worker_timeout_seconds=600,methods=list(exp.METHODS),primary_reference='range_response',
    decision_rule='negative upper endpoint of equal-board mean candidate-minus-reference interval',
    sensitivity_rule='negative upper endpoint in all four textures and every leave-one-board-out panel',
    preflight='Sigmoid/capacity/endpoints/suit invariance passed; selection unscored, disjoint and reproducible.')
assert len(plan['cases'])==96 and not Path(plan['output']).exists()
write(HERE/'plan.json',plan)
print(json.dumps(dict(plan_sha256=digest(HERE/'plan.json'),candidate_sha256=digest(HERE/'candidate.json'),
                     pins=len(pins),excluded_boards=len(excluded),boards=boards),indent=2))
