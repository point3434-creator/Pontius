"""Use sealed research helpers without invoking their experiments."""
from pathlib import Path
import sys

ROOT = Path('D:/Pontius-worktrees/eval-runner-consolidation')
HISTORY = ROOT/'experiments/river-abstraction-study'
PRIOR = HISTORY/'multibet-size-confirmation-001'
sys.path.insert(0, str(PRIOR/'verification-tools'))
from support import c, m, d
