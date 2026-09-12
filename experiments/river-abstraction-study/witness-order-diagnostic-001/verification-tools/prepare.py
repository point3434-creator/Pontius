"""Validate projection and freeze the diagnostic before any new cell is scored."""
from environment import ROOT,PRIOR,read,write,digest
from datetime import datetime,timezone
from pathlib import Path
import ast
import subprocess
import sys
import experiment as e

HERE=Path(__file__).parent
assert Path(e.__file__).resolve()==(HERE/'experiment.py').resolve()
SEAL='078b3e0ab9962d99102eb4d315a08dc3f33eeca2ba0ff1a6bdb2e179ed446f23'
assert digest(PRIOR/'milestone-manifest.json')==SEAL
pins={str(PRIOR/'milestone-manifest.json'):SEAL}
for name,h in read(PRIOR/'milestone-manifest.json').items():
    assert digest(PRIOR/name)==h,name
    pins[str(PRIOR/name)]=h
old=read(PRIOR/'plan.json')
for path,h in old['pins'].items():
    assert digest(path)==h,path
    pins[path]=h
red_code="import importlib.util,sys,runpy; s=importlib.util.spec_from_file_location('projection','projection-red.py'); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); sys.modules['projection']=m; runpy.run_path('test_projection.py',run_name='__main__')"
receipts={}
for mode,command,expected in (
    ('red-confirmation',[sys.executable,'-B','-W','error::ResourceWarning','-c',red_code],1),
    ('green-confirmation',[sys.executable,'-B','-W','error::ResourceWarning','test_projection.py'],0)):
    result=subprocess.run(command,cwd=HERE,capture_output=True,timeout=30)
    assert result.returncode==expected,(mode,result.stderr)
    (HERE/(mode+'.txt')).write_bytes(result.stdout+result.stderr)
    receipts[mode]=dict(command=command,exit=result.returncode,expected_exit=expected)
write(HERE/'preflight.json',dict(passed=True,tests=5,exhaustive_triplets=1125,
    python=sys.version,scored_rehearsal=False,receipts=receipts))
e.base.helpers()
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
for path in HERE.iterdir():
    if path.is_file() and path.name!='plan.json':pins[str(path)]=digest(path)
    if path.suffix=='.py':ast.parse(path.read_bytes())
plan=dict(schema='caller-order-diagnostic-v1',milestone=e.NAME,
    user_words_verbatim="If you know what's next design and run please",
    recorded_at_utc=datetime.now(timezone.utc).isoformat(),source_head=head,
    predecessor=str(PRIOR),predecessor_manifest_sha256=SEAL,
    evaluation_cases=old['evaluation_cases'],bets=[5,10],evaluation_cells=64,
    primary_bet=5,fit_tasks=0,lp_calls=128,methods=list(e.METHODS),
    checkpoints=list(e.CHECKPOINTS),phase_timeout_seconds=900,
    output='D:/Pontius-training/river-abstraction-study/'+e.NAME,pins=pins)
assert not Path(plan['output']).exists()
write(HERE/'plan.json',plan);e.bindings(plan)
print(dict(plan_sha256=digest(HERE/'plan.json'),pins=len(pins),head=head))
