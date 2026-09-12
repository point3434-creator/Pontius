"""Pinned research and external trainer interfaces; no training invocation."""
from pathlib import Path
import sys

ROOT = Path('D:/Pontius-worktrees/eval-runner-consolidation')
HISTORY = ROOT/'experiments/river-abstraction-study'
PRIOR = HISTORY/'multibet-size-confirmation-001'
EXTERNAL = Path('D:/Projects/pluribus-lite')
BASELINE = Path('D:/Pontius-training/six-max/milestones/baseline-000')
# Load prior support under another name to avoid this module's own name.
import importlib.util

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module

sys.path.insert(0, str(PRIOR/'verification-tools'))
old = load('transfer_old_support', PRIOR/'verification-tools/support.py')
c, m, d = old.c, old.m, old.d
# size_repair imports support; provide its three frozen dependencies here.
r = load('transfer_repair', PRIOR/'verification-tools/size_repair.py')
sys.path.insert(0, str(EXTERNAL))
PHE = EXTERNAL/'venv/Lib/site-packages/phevaluator'
# Reuse the existing CPython 3.14 evaluator without importing the other environment's NumPy.
load('phevaluator', PHE/'__init__.py')
from pluribus_lite.engine import NLHE, BetMenu
from pluribus_lite.abstraction import BucketAssigner
from pluribus_lite.mccfr import BlueprintPolicy
from pluribus_lite import public_range, river_capture, evaluator
from pluribus_lite.river_solver import ComboIndex, BoardEval
np = m.np
