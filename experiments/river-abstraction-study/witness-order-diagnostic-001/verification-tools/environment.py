"""Reuse frozen experiment components without persistent path shadowing."""
import os
for name in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[name]='1'
import importlib.util
from pathlib import Path
import sys
ROOT=Path('D:/Pontius-worktrees/eval-runner-consolidation')
PRIOR=ROOT/'experiments/river-abstraction-study/witness-ordinal-001'
path=str(PRIOR/'verification-tools');sys.path.insert(0,path)
spec=importlib.util.spec_from_file_location('sealed_ordinal',PRIOR/'verification-tools/experiment.py')
old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old);sys.path.remove(path)
np,opt,base,budget,transfer=old.np,old.opt,old.base,old.budget,old.transfer
read,write,digest=old.read,old.write,old.digest
