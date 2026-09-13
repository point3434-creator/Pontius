"""Direct access to frozen numerical and acceptance components."""
from pathlib import Path
import importlib.util
import sys

ROOT = Path('D:/Pontius-worktrees/eval-runner-consolidation')
HISTORY = ROOT/'experiments/river-abstraction-study'
PRIOR = HISTORY/'witness-guarded-repair-confirmation-001'


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    sys.modules[name] = result
    spec.loader.exec_module(result)
    return result


base = load('base', PRIOR/'verification-tools/base.py')
c = base.c
gate = load('frozen_security_gate', PRIOR/'verification-tools/gate.py')
