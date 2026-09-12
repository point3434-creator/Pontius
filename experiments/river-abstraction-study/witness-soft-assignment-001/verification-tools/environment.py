"""Pinned research imports; no earlier experiment driver is executed."""
import os
from pathlib import Path
import sys

for name in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS',
             'NUMEXPR_NUM_THREADS'):
    os.environ[name] = '1'
ROOT = Path('D:/Pontius-worktrees/eval-runner-consolidation')
sys.path.insert(0, str(ROOT / 'src'))
import numpy as np
import scipy
from pontius.river_abstraction_study import PayoffGame, anchored_clusters, _regret_match
from pontius import river_group_optimality as opt
from pontius.river import RiverHoldem
from pontius.river_witness_distillation import design, raw_features
from pontius.river_abstraction_study import uniform_equities

if sys.version_info[:3] != (3, 14, 6):
    raise RuntimeError('CPython 3.14.6 required')
if np.__version__ != '2.5.2' or scipy.__version__ != '1.18.0':
    raise RuntimeError('pinned NumPy/SciPy required')
