# River time-quality experiment: ready build

The next study is built and validated; the full campaign has not run.
It asks whether additional graph-solver iterations improve exact audited error
within accounted budgets of 3, 5, 10 and 15 seconds.

The design fixes 2,048 / 4,096 / 8,192 / 16,384 iterations, both expanded river
games and three repeats. Select the latest affordable checkpoint without
consulting error. Preserve budget misses and any worsening at later checkpoints.
Preparation, observed process overhead and an independent audit are charged.
This is an accounting comparison, not a live action-clock guarantee.

Validation completed on Python 3.14.6: six selector test methods passed; two
2,048-iteration solves using the 16,384 horizon matched retained policy bytes;
two independent rational audits reproduced their previous exact errors.
These are runner-validation facts, not a new research result. The main campaign
will produce six trajectories and 24 checkpoint audits, under the bound plan.

Source and input identities, the design, validation receipts and dependency copies
are retained in the build. The native cuBLAS runtime is pinned but not redistributed.
The full campaign must start from the author directory because frozen imports and
input paths are bound there. No solver implementation was duplicated or changed.

Launch command, after the user requests the full comparison:

```powershell
& 'C:/Users/point/AppData/Local/Python/pythoncore-3.14-64/python.exe' `
  -I -S -B -W error::ResourceWarning `
  'D:/Pontius/experiments/river-time-quality-001/launch.py' campaign.py execute `
  6da2525fc78e836b6d7fd412ec08c415636ea1c21bf4074a87ea14657971bc5a run
```

Preflight results remain in preflight/; the campaign creates a new run/ directory.
No commit, push, strategy adoption or bot integration occurred.
