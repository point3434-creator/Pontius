"""Freeze all choices and source bindings before any retained scoring."""
import ast
from datetime import datetime,timezone
import json
from pathlib import Path
import subprocess
import sys
from bridge import ROOT,PRIOR,base,read,write,digest,transfer
import experiment as e

HERE=Path(__file__).parent
SEAL='bba5346e6b12db621cf7e96239436438d9c7316e8538756120b33177798b441f'
assert digest(PRIOR/'milestone-manifest.json')==SEAL
pins={str(PRIOR/'milestone-manifest.json'):SEAL}
for name,h in read(PRIOR/'milestone-manifest.json').items():
    assert digest(PRIOR/name)==h,name
    pins[str(PRIOR/name)]=h
for path,h in read(PRIOR/'plan.json')['pins'].items():
    assert digest(path)==h,path
    pins[path]=h
tool=base.helpers()
old=read(ROOT/'experiments/river-abstraction-study/witness-preference-001/plan.json')
conf=read(transfer.PRIOR/'plan.json')
excluded=sorted(set(tuple(b) for b in conf['excluded_boards']+conf['boards']))
assert len(excluded)==36
boards,receipt=e.select(excluded,tool.pilot)
training=[c for c in old['training_cases'] if c['pool']<2]
assert len(training)==32
for module in list(sys.modules.values()):
    p=getattr(module,'__file__',None)
    if p:
        p=Path(p).resolve()
        if p.suffix=='.py' and p.is_relative_to(ROOT):pins[str(p)]=digest(p)
git=['C:/Program Files/Git/cmd/git.exe','-c',f'safe.directory={ROOT}','-C',str(ROOT)]
head=subprocess.check_output(git+['rev-parse','HEAD'],text=True).strip()
status=subprocess.check_output(git+['status','--porcelain'],text=True)
modified={n:digest(ROOT/n) for n in subprocess.check_output(git+['diff','--name-only'],text=True).splitlines()
          if (ROOT/n).is_file()}
write(HERE/'worktree-before.json',dict(head=head,status=status,modified_tracked_files=modified))
write(HERE/'preflight.json',dict(passed=True,red_exit=1,red_reason='missing bet input',
    model_tests=8,solver_tests=6,existing_tests=13,green_exit=0,scored_panel_rehearsal=False,
    import_collision='Caught by preflight, fixed before freeze; failed receipt retained',
    python='3.14.6',receipts=['red.txt','green.txt','preflight-import-error.txt',
                             'solver-preflight.txt','existing-preflight.txt']))
for p in HERE.iterdir():
    if p.is_file() and p.name not in ('plan.json',):pins[str(p)]=digest(p)
    if p.suffix=='.py':ast.parse(p.read_bytes())
plan=dict(schema='bet-conditioned-preference-pilot-v1',milestone=e.SEED,
    user_words_verbatim="Let's run it",recorded_at_utc=datetime.now(timezone.utc).isoformat(),
    source_head=head,predecessor=str(PRIOR),predecessor_manifest_sha256=SEAL,
    training_cases=training,excluded_boards=[list(b) for b in excluded],
    boards=boards,selection_receipt=receipt,evaluation_cases=e.grid(boards,tool),
    bets=[5,10],training_cells=64,evaluation_cells=64,fit_tasks=12,lp_calls=1280,
    methods=list(e.METHODS),solver_methods=list(e.SOLVERS),checkpoints=list(e.CHECKPOINTS),
    output='D:/Pontius-training/river-abstraction-study/witness-bet-conditioned-001',
    worker_timeout_seconds=1200,verifier_timeout_seconds=1200,
    script_sha256=digest(HERE/'experiment.py'),pins=pins)
assert not Path(plan['output']).exists()
write(HERE/'plan.json',plan)
e.bindings(plan)
print(json.dumps(dict(plan_sha256=digest(HERE/'plan.json'),pins=len(pins),
    training_cells=64,evaluation_cells=64,boards=boards,head=head),indent=2))
