"""Load the sealed bet-conditioned experiment without leaving an import override."""
import importlib.util
from pathlib import Path
import sys

ROOT=Path('D:/Pontius-worktrees/eval-runner-consolidation')
PRIOR=ROOT/'experiments/river-abstraction-study/witness-bet-conditioned-001'
path=str(PRIOR/'verification-tools')
sys.path.insert(0,path)
spec=importlib.util.spec_from_file_location('sealed_conditioned',PRIOR/'verification-tools/experiment.py')
parent=importlib.util.module_from_spec(spec)
spec.loader.exec_module(parent)
sys.path.remove(path)
np,opt,base,budget,transfer=parent.np,parent.opt,parent.base,parent.budget,parent.transfer
read,write,digest,pref=parent.read,parent.write,parent.digest,parent.pref
RegretBR,anchored_clusters,action_advantages=parent.RegretBR,parent.anchored_clusters,parent.action_advantages
model=parent.model
