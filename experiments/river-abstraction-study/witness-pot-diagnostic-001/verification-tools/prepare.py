"""Seal the diagnostic design and all input bytes before the retained invocation."""
from datetime import datetime,timezone
import ast
import difflib
import json
from pathlib import Path
import subprocess
import sys

from context import ROOT,PRIOR,read,write,digest,base,select

HERE=Path(__file__).parent
SEAL='7bd4993682435a0080e0ce407efd3d7aaf417209861bc4a138a8cc458791d96f'
assert digest(PRIOR/'milestone-manifest.json')==SEAL
pins={str(PRIOR/'milestone-manifest.json'):SEAL}
for name,h in read(PRIOR/'milestone-manifest.json').items():
    assert digest(PRIOR/name)==h,name
    pins[str(PRIOR/name)]=h
old=read(PRIOR/'plan.json')
for path,h in old['pins'].items():
    assert digest(path)==h,path
    pins[path]=h
base.helpers()
for module in list(sys.modules.values()):
    path=getattr(module,'__file__',None)
    if path:
        path=Path(path).resolve()
        if path.suffix=='.py' and path.is_relative_to(ROOT):pins[str(path)]=digest(path)
red=HERE/'br-red.py'
green=HERE/'br.py'
patch=''.join(difflib.unified_diff(red.read_text().splitlines(True),green.read_text().splitlines(True),
                                fromfile='br-red.py',tofile='br.py'))
with (HERE/'red-to-green.diff').open('x',encoding='utf-8',newline='\n') as f:f.write(patch)
preflight=dict(passed=True,python='3.14.6',scored_panel_rehearsal=False,
    red=dict(exit=1,source_sha256=digest(red),test='test_first_update_uses_unrestricted_best_responses',
        observed='uniform [0.5,0.5], expected [1,0]',
        command=f'{sys.executable} -B -W error::ResourceWarning {HERE}/test_br.py '
                'BRTests.test_first_update_uses_unrestricted_best_responses'),
    green=dict(exit=0,source_sha256=digest(green),tests=6,seconds=.480,
               command=f'{sys.executable} -B -W error::ResourceWarning {HERE}/test_br.py'),
    existing=dict(exit=0,tests=13,seconds=.92,
        command=f'{sys.executable} -B -W error::ResourceWarning -m pytest '
        'tests/test_river_abstraction_study.py::PayoffTests '
        'tests/test_river_group_optimality.py::OptimalityTests -q -p no:cacheprovider'),
    provenance='Executed before freeze; console output in tool history. RED method unchanged; '
        'GREEN suite additionally includes the witness-feature test. RED source retained byte-exact.')
write(HERE/'preflight.json',preflight)
git=['C:/Program Files/Git/cmd/git.exe','-c',f'safe.directory={ROOT}','-C',str(ROOT)]
head=subprocess.check_output(git+['rev-parse','HEAD'],text=True).strip()
status=subprocess.check_output(git+['status','--porcelain'],text=True)
modified={name:digest(ROOT/name) for name in subprocess.check_output(git+['diff','--name-only'],text=True).splitlines()
          if (ROOT/name).is_file()}
write(HERE/'worktree-before.json',dict(head=head,status=status,modified_tracked_files=modified))
for name in ('design.md','context.py','br.py','br-red.py','test_br.py','summary-audit.py','prepare.py',
             'red-to-green.diff','preflight.json','worktree-before.json'):
    pins[str(HERE/name)]=digest(HERE/name)
for p in HERE.glob('*.py'):ast.parse(p.read_bytes())
cases=select(old['cases'])
assert len(cases)==60
plan=dict(schema='pot-failure-diagnostic-v1',milestone='witness-pot-diagnostic-001',
    user_words_verbatim="Let's move on design and run please",recorded_at_utc=datetime.now(timezone.utc).isoformat(),
    source_head=head,predecessor=str(PRIOR),predecessor_manifest_sha256=SEAL,
    cases=cases,solver_methods=['ordinary_preference','range_response'],algorithms=['cfr','br'],
    checkpoints=[1000,10000,50000],oracle_variants=['half_witness','pot_witness'],
    new_lp_calls=96,new_solver_trajectories=240,model_fits=0,
    worker_timeout_seconds=1200,verifier_timeout_seconds=1200,
    candidate_sha256=old['candidate_sha256'],
    output='D:/Pontius-training/river-abstraction-study/witness-pot-diagnostic-001',
    script_sha256=digest(HERE/'experiment.py'),pins=pins)
assert not Path(plan['output']).exists()
write(HERE/'plan.json',plan)
print(json.dumps(dict(plan_sha256=digest(HERE/'plan.json'),pins=len(pins),cases=len(cases),head=head),indent=2))
