"""Import only the preserved research chain."""
import importlib.util
from pathlib import Path
import sys

ROOT=Path('D:/Pontius-worktrees/eval-runner-consolidation')
PRIOR=ROOT/'experiments/river-abstraction-study/witness-pot-diagnostic-001'
sys.path.insert(0,str(PRIOR/'verification-tools'))
spec=importlib.util.spec_from_file_location('pot_diagnostic',PRIOR/'verification-tools/experiment.py')
diag=importlib.util.module_from_spec(spec)
spec.loader.exec_module(diag)
sys.path.remove(str(PRIOR/'verification-tools'))
np,opt,base,budget,transfer=diag.np,diag.opt,diag.base,diag.budget,diag.transfer
read,write,digest=diag.read,diag.write,diag.digest
pref=budget.pref
RegretBR=diag.RegretBR
anchored_clusters=diag.anchored_clusters
action_advantages=diag.action_advantages
