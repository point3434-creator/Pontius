# Bound distillation execution request

One execution of plan.json under SHA-256:
47b26fc64aa3b2ddb36ebe11a02d16253b240a61672cff162c51af689728e524

Fit two fixed 78-by-4 coefficient ridge models on the 48 verified observed cases
from witness-pilot-001. No tuning or model selection. Evaluate 48 new cases across
eight reserved boards, three pools, two regimes, 96 holdings per seat. Compare
predicted groups with range controls and fresh exact-witness groups at matched
capacity. 576 new LP calls, including new control/oracle evaluation. Training fits
and certificate verification add no LP calls. Historical teacher cost is separate.

One worker, one BLAS thread, 1,200-second worker timeout; five seconds and 10,000
iterations per LP. Parent reconstruction/refitting, verification and I/O are outside
the worker bound. No process RSS cap. No runtime or memory guarantee is implied.
All cases and regressions retained. No partial-population headline or retry.

Output: D:/Pontius-training/river-abstraction-study/witness-distillation-001
Python 3.14.6 / NumPy 2.5.2 / SciPy 1.18.0 in the pinned existing environment.
No actual model fit or reserved-board score has occurred. Separate controller
approval is required; it does not authorize commit, push or further experiments.
