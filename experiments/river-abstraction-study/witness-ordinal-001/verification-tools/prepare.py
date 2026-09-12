"""Seal the ordinal pilot without scoring its fresh evaluation panel."""
import ast
from datetime import datetime,timezone
import json
from pathlib import Path
import subprocess
import sys
from loader import ROOT,PRIOR,base,read,write,digest
import experiment as e

HERE=Path(__file__).parent
SEAL='06bc9a4baae10e0970fd20f2bf439f2c21fbd4ebbc34a488b3e06bdbaf37c8ab'
assert digest(PRIOR/'milestone-manifest.json')==SEAL
pins={str(PRIOR/'milestone-manifest.json'):SEAL}
for name,h in read(PRIOR/'milestone-manifest.json').items():
    assert digest(PRIOR/name)==h,name
    pins[str(PRIOR/name)]=h
old=read(PRIOR/'plan.json')
for path,h in old['pins'].items():
    assert digest(path)==h,path
    pins[path]=h
tool=base.helpers()
excluded=sorted(set(tuple(b) for b in old['excluded_boards']+old['boards']))
assert len(excluded)==44
boards,receipt=e.select(excluded,tool.pilot)
for module in list(sys.modules.values()):
    path=getattr(module,'__file__',None)
    if path:
        path=Path(path).resolve()
        if path.suffix=='.py' and path.is_relative_to(ROOT):pins[str(path)]=digest(path)
git=['C:/Program Files/Git/cmd/git.exe','-c',f'safe.directory={ROOT}','-C',str(ROOT)]
head=subprocess.check_output(git+['rev-parse','HEAD'],text=True).strip()
status=subprocess.check_output(git+['status','--porcelain'],text=True)
modified={n:digest(ROOT/n) for n in subprocess.check_output(git+['diff','--name-only'],text=True).splitlines() if (ROOT/n).is_file()}
write(HERE/'worktree-before.json',dict(head=head,status=status,modified_tracked_files=modified))
write(HERE/'preflight.json',dict(passed=True,red_exit=1,red_reason='repeated sign labels omit magnitude cutoffs',
    ordinal_tests=6,fit_boundary_tests=8,solver_tests=6,green_exit=0,scored_panel_rehearsal=False,
    python='3.14.6',receipts=['red.txt','green.txt','model-preflight.txt','solver-preflight.txt']))
for path in HERE.iterdir():
    if path.is_file() and path.name!='plan.json':pins[str(path)]=digest(path)
    if path.suffix=='.py':ast.parse(path.read_bytes())
plan=dict(schema='ordinal-preference-pilot-v1',milestone=e.SEED,user_words_verbatim="Let's design and run it!",
    recorded_at_utc=datetime.now(timezone.utc).isoformat(),source_head=head,
    predecessor=str(PRIOR),predecessor_manifest_sha256=SEAL,training_cases=old['training_cases'],
    excluded_boards=[list(b) for b in excluded],boards=boards,selection_receipt=receipt,
    evaluation_cases=e.grid(boards,tool),bets=[5,10],training_cells=64,evaluation_cells=64,
    fit_tasks=18,lp_calls=1024,methods=list(e.METHODS),solver_methods=list(e.SOLVERS),
    thresholds=list(e.ordinal.THRESHOLDS),checkpoints=list(e.CHECKPOINTS),
    output='D:/Pontius-training/river-abstraction-study/witness-ordinal-001',
    worker_timeout_seconds=1200,verifier_timeout_seconds=1200,script_sha256=digest(HERE/'experiment.py'),pins=pins)
assert not Path(plan['output']).exists()
write(HERE/'plan.json',plan);e.bindings(plan)
print(json.dumps(dict(plan_sha256=digest(HERE/'plan.json'),pins=len(pins),boards=boards,head=head),indent=2))
