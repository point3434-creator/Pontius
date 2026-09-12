"""Load frozen numerical components without running an earlier experiment."""
from pathlib import Path
import importlib.util
import sys

ROOT = Path('D:/Pontius-worktrees/eval-runner-consolidation')
HISTORY = ROOT/'experiments/river-abstraction-study'
PRIOR = HISTORY/'witness-second-guarded-repair-001'
spec = importlib.util.spec_from_file_location('frozen_second_support',
                                            PRIOR/'verification-tools/support.py')
support = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = support
spec.loader.exec_module(support)
c, gate = support.c, support.gate
