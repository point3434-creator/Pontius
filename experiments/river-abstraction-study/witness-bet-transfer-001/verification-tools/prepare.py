"""Verify all predecessors and freeze the next experiment before scoring."""
from datetime import datetime,timezone
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

HERE=Path(__file__).parent
spec=importlib.util.spec_from_file_location('transfer',HERE/'experiment.py')
exp=importlib.util.module_from_spec(spec)
spec.loader.exec_module(exp)
ROOT,BUDGET=exp.ROOT,exp.BUDGET
read,write,digest=exp.read,exp.write,exp.digest
seal='5ba746aa32ca8ba154e131287edb8212cc6743fcce95dcfc76d08a503d2be7a8'
assert digest(BUDGET/'milestone-manifest.json')==seal
pins={str(BUDGET/'milestone-manifest.json'):seal}
for name,h in read(BUDGET/'milestone-manifest.json').items():
    assert digest(BUDGET/name)==h,name
    pins[str(BUDGET/name)]=h
old=read(BUDGET/'plan.json')
for path,h in old['pins'].items():
    assert digest(path)==h,path
    pins[path]=h
exp.base.helpers()
for module in list(sys.modules.values()):
    path=getattr(module,'__file__',None)
    if path:
        path=Path(path).resolve()
        if path.suffix=='.py' and path.is_relative_to(ROOT):pins[str(path)]=digest(path)
for name in ('design.md','prepare.py','summary-audit.py'):
    pins[str(HERE/name)]=digest(HERE/name)
for name in ('test_river_abstraction_study.py','test_river_group_optimality.py'):
    pins[str(ROOT/'tests'/name)]=digest(ROOT/'tests'/name)
git=['C:/Program Files/Git/cmd/git.exe','-c',f'safe.directory={ROOT}','-C',str(ROOT)]
head=subprocess.check_output(git+['rev-parse','HEAD'],text=True).strip()
status=subprocess.check_output(git+['status','--porcelain'],text=True)
tracked={name:digest(ROOT/name) for name in subprocess.check_output(
    git+['diff','--name-only'],text=True).splitlines() if (ROOT/name).is_file()}
write(HERE/'worktree-before.json',dict(head=head,status=status,modified_tracked_files=tracked))
pins[str(HERE/'worktree-before.json')]=digest(HERE/'worktree-before.json')
preflight=dict(passed=True,python='3.14.6',scored_panel_rehearsal=False,
    synthetic=dict(exit=0,command=f'{sys.executable} -B -W error::ResourceWarning '
        f'{HERE}/experiment.py self-test',checks='public tree BR at three sizes; called stakes; '
        'feature identity; ties; invalid bet refusals'),
    existing=dict(exit=0,tests_passed=13,seconds=.92,
        command=f'{sys.executable} -B -W error::ResourceWarning -m pytest '
        'tests/test_river_abstraction_study.py::PayoffTests '
        'tests/test_river_group_optimality.py::OptimalityTests -q -p no:cacheprovider'),
    provenance='Executed in the author session before freeze; console outputs in tool history.')
write(HERE/'preflight.json',preflight)
pins[str(HERE/'preflight.json')]=digest(HERE/'preflight.json')
plan=dict(schema='frozen-bet-transfer-v1',milestone='witness-bet-transfer-001',
    user_words_verbatim="Let's design and run that test",recorded_at_utc=datetime.now(timezone.utc).isoformat(),
    source_head=head,predecessor=str(BUDGET),predecessor_manifest_sha256=seal,
    candidate_sha256=digest(exp.PRIOR/'candidate.json'),cases=old['cases'],
    bets=list(exp.BETS),methods=list(exp.METHODS),iterations=[100,1000,10000],
    new_lp_calls=1152,new_cfr_trajectories=576,model_fits=0,
    worker_timeout_seconds=1200,verifier_timeout_seconds=1200,
    output='D:/Pontius-training/river-abstraction-study/witness-bet-transfer-001',
    script_sha256=digest(HERE/'experiment.py'),pins=pins)
assert not Path(plan['output']).exists()
write(HERE/'plan.json',plan)
print(json.dumps(dict(plan_sha256=digest(HERE/'plan.json'),pins=len(pins),head=head),indent=2))
