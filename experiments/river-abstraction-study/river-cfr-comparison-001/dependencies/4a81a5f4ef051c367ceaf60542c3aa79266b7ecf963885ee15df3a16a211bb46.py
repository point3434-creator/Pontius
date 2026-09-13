"""Reuse the frozen game construction, repair and solver components."""
from pathlib import Path
import importlib.util
import sys

ROOT = Path('D:/Pontius-worktrees/eval-runner-consolidation')
HISTORY = ROOT/'experiments/river-abstraction-study'
PRIOR = HISTORY/'witness-group-repair-confirmation-001'
spec = importlib.util.spec_from_file_location('frozen_confirmation',
    PRIOR/'verification-tools/confirmation.py')
c = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = c
spec.loader.exec_module(c)
