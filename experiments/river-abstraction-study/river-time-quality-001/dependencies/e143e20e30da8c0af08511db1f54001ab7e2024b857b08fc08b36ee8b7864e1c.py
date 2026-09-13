"""Direct library imports and one frozen mathematical component."""
import os
from pathlib import Path
import sys
import importlib.util

for name in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS',
             'NUMEXPR_NUM_THREADS'):
    os.environ[name] = '1'
ROOT = Path('D:/Pontius-worktrees/eval-runner-consolidation')
PRIOR = ROOT/'experiments/river-abstraction-study/witness-soft-assignment-001'
sys.path.insert(0, str(ROOT/'src'))
import numpy as np
import scipy
from pontius.river_abstraction_study import PayoffGame, _regret_match
from pontius.river import RiverHoldem
from pontius import river_group_optimality as opt

if sys.version_info[:3] != (3, 14, 6):
    raise RuntimeError('Python 3.14.6 required')
if np.__version__ != '2.5.2' or scipy.__version__ != '1.18.0':
    raise RuntimeError('pinned NumPy/SciPy required')
spec = importlib.util.spec_from_file_location('frozen_soft_math',
                                             PRIOR/'verification-tools/soft.py')
core = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = core
spec.loader.exec_module(core)
