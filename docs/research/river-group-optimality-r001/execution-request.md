# Fixed-group diagnostic execution request

This is a request for one invocation of the current reviewed plan; it is not an
authorization record. The observed-case diagnostic has not run.

Plan: docs/research/river-group-optimality-r001/plan.json
SHA-256: de07461ea9364a4fb40d0bce72a506549bc30ac609761bb0bc57ff4600c3b11c

The plan fixes all eight observed development/holdout cases, 96 hands per seat,
four unchanged groupings per case, 32 group-constrained solutions and comparison
against all 96 saved profiles. Each solution uses two one-sided LPs, so the worker
performs 64 LP calls. No new board, grouping, feature, CFR or neural training run.

Bounds: sequential LP calls, each with a five-second solver limit and 10,000
iterations; one worker with a 300-second wall timeout. Parent rational verification
and I/O are outside the worker timeout. No process RSS cap is imposed. Failed output
directories remain evidence and are never reused or retried automatically.

Output: D:\Pontius-training\river-abstraction-study\group-optimality-001
Interpreter: D:\Pontius\tmp\group-opt-author\venv\Scripts\python.exe
Versions: Python 3.14.6, NumPy 2.5.2, SciPy 1.18.0.

Each saddle certificate must be at most 1e-8 chips wide, recomputed in exact rational
arithmetic on the encoded binary64 payoff numbers. Development and previously
observed holdout results are reported separately. This is a diagnosis of those
fixed cases, not new holdout confirmation or evidence of six-max playing strength.

The current source, plan and 32 retained input-file hashes are checked before
launch and again before completion. The original milestones remain read-only.
Commit, push and any later experiment require their own authorization.
