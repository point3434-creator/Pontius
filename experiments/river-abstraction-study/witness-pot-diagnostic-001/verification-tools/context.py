"""Read-only imports from the sealed transfer study."""
import importlib.util
from pathlib import Path

ROOT=Path('D:/Pontius-worktrees/eval-runner-consolidation')
PRIOR=ROOT/'experiments/river-abstraction-study/witness-bet-transfer-001'
spec=importlib.util.spec_from_file_location('transfer',PRIOR/'verification-tools/experiment.py')
transfer=importlib.util.module_from_spec(spec)
spec.loader.exec_module(transfer)
budget=transfer.budget
np,opt,base=transfer.np,transfer.opt,transfer.base
read,write,digest=transfer.read,transfer.write,transfer.digest
from pontius.river_abstraction_study import CFR,PayoffGame,_regret_match,anchored_clusters
from pontius.river_witness_groups import action_advantages


def select(cases):
    return [c for c in cases if c['regime']=='polarized' or c['texture']=='multiple-pairs-or-trips']
