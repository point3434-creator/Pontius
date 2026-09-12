"""Freeze inputs before any benchmark trajectory is run."""
from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

HERE=Path(__file__).parent
spec=importlib.util.spec_from_file_location('budget',HERE/'experiment.py')
exp=importlib.util.module_from_spec(spec)
spec.loader.exec_module(exp)
read,write,digest=exp.read,exp.write,exp.digest
ROOT,PRIOR=exp.ROOT,exp.PRIOR
seal='59a13dcab4d8a497004ebb138adee1f5502b32d276fba406e2fb724f1a116b22'
assert digest(PRIOR/'milestone-manifest.json')==seal
pins={str(PRIOR/'milestone-manifest.json'):seal}
for name,h in read(PRIOR/'milestone-manifest.json').items():
    assert digest(PRIOR/name)==h,name
    pins[str(PRIOR/name)]=h
old=read(PRIOR/'plan.json')
for path,h in old['pins'].items():
    assert digest(path)==h,path
    pins[path]=h
tool=exp.base.helpers()
for module in list(sys.modules.values()):
    path=getattr(module,'__file__',None)
    if path:
        path=Path(path).resolve()
        if path.suffix=='.py' and path.is_relative_to(ROOT):
            pins[str(path)]=digest(path)
for name in ('design.md','prepare.py','summary-audit.py'):
    pins[str(HERE/name)]=digest(HERE/name)
test=ROOT/'tests/test_river_abstraction_study.py'
pins[str(test)]=digest(test)
git=['C:/Program Files/Git/cmd/git.exe','-c',f'safe.directory={ROOT}','-C',str(ROOT)]
head=subprocess.check_output(git+['rev-parse','HEAD'],text=True).strip()
status=subprocess.check_output(git+['status','--porcelain'],text=True)
write(HERE/'worktree-before.json',dict(head=head,status=status,
      unrelated_files={name:digest(ROOT/name) for name in ('STATUS.md','execution_journal.jsonl')}))
pins[str(HERE/'worktree-before.json')]=digest(HERE/'worktree-before.json')
preflight=dict(passed=True,python='3.14.6',
    synthetic=dict(exit=0,command=f'{sys.executable} -B -W error::ResourceWarning '
                   f'{HERE}/experiment.py self-test',
                   checks='scalar BR; pre-boundary policy; multiple crossed budgets; setup miss; equality'),
    existing_tests=dict(exit=0,passed=7,seconds=.33,
        command=f'{sys.executable} -B -W error::ResourceWarning -m pytest '
        'tests/test_river_abstraction_study.py::PayoffTests -q -p no:cacheprovider'),
    provenance='Executed in the author session before freeze; outputs retained in tool history.',
    scored_rehearsal=False)
write(HERE/'preflight.json',preflight)
pins[str(HERE/'preflight.json')]=digest(HERE/'preflight.json')
plan=dict(schema='witness-solver-budget-v1',milestone='witness-solver-budget-001',
    user_words_verbatim="Let's design and run the test",recorded_at_utc=datetime.now(timezone.utc).isoformat(),
    source_head=head,prior=str(PRIOR),prior_manifest_sha256=seal,
    candidate_sha256=digest(PRIOR/'candidate.json'),cases=old['cases'],methods=list(exp.METHODS),
    iterations=list(exp.ITERATIONS),seconds=list(exp.BUDGETS),timed_repetitions=3,
    expected_trajectories=1152,expected_checkpoints=3456,model_fits=0,lp_calls=0,
    worker_timeout_seconds=1200,parent_timeout_seconds=900,
    primary_rule='both equal-board mean deltas below -1e-10: 10000 iterations and 0.5 seconds',
    output='D:/Pontius-training/river-abstraction-study/witness-solver-budget-001',
    script_sha256=digest(HERE/'experiment.py'),pins=pins)
assert not Path(plan['output']).exists()
write(HERE/'plan.json',plan)
print(json.dumps(dict(plan_sha256=digest(HERE/'plan.json'),pins=len(pins),head=head),indent=2))
