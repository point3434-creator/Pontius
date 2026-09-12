# Fresh-board pilot execution request

One execution of plan.json, SHA-256:
535a3fa5b4d55d8bc6cc29763c63b5ab41f89cf0ea190bca90f9c00a5a8c9d2c

Eight fresh boards, three 96-holding pools per seat per board, two regimes:
48 cases, 480 LP calls including newly generated witness banks. The grouping
formula and capacity controls stay fixed. All cases are required. Report board
and pool variation descriptively; no all-board significance or six-max claim.

Worker timeout 1,200 seconds; each LP five seconds and 10,000 iterations.
One sequential worker and one BLAS thread. Parent reconstruction and I/O are
outside the worker timeout. No process RSS cap. This is a stop bound, not a
runtime forecast; prior runs using retained witness banks are not comparable.

Output: D:/Pontius-training/river-abstraction-study/witness-pilot-001
Python: D:/Pontius/tmp/group-opt-author/venv/Scripts/python.exe (3.14.6)
NumPy 2.5.2 / SciPy 1.18.0. No retry or partial-population success.
No pilot invocation has occurred and no authorization file exists. This request
does not authorize commit, push, adoption or a subsequent experiment.
