# Development screen execution request

One execution of the reviewed plan.json, SHA-256:
9581a2a8e8d74d9d66e31abed59a61cff7625b769be4521a303b0c343f0ed855

Four development cases, 96 hands per seat, one fixed witness_advantage grouping
per case at the existing occupied capacity. Eight LP calls total. No new CFR
training, holdout evaluation, iterative refinement, parameter sweep or fallback
selection. Primary comparison is the mean grouping floor versus range_equity;
range_response is secondary, with every case and all controls retained.

Bound worker: 120 seconds wall time; each LP five seconds and 10,000 iterations.
Parent verification and I/O are outside the worker timeout. No process RSS cap.
The bank contains solver-assisted information and its previous creation cost is
excluded. This is a development screen, not a generalization or efficiency claim.

Output: D:/Pontius-training/river-abstraction-study/witness-groups-development-001
Python: D:/Pontius/tmp/group-opt-author/venv/Scripts/python.exe (3.14.6)
NumPy 2.5.2, SciPy 1.18.0. Original sources and milestone data are read-only.
No invocation has occurred; no authorization file exists. Approval of this run
does not authorize commit, push, deployment or a subsequent experiment.
