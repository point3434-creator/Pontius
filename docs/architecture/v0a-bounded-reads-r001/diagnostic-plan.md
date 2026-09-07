# Successor diagnostic definition, fixed before timing

After correctness qualification, run v2 once unprofiled and once recursively
profiled from the frozen candidate, actual Python 3.11.15, fresh D-local roots.
Use exactly the performance-pass-20260907-001 request definition: seed SHA256 of
`pontius-focused-performance-20260907-001`, one deal, one fixed mixed lineup, all
six positions and both existing policies (12 trials), 60 s trial allowance and
900 s shared allowance, 1200 s outer diagnostic bound. New run identities start
`brv2-`. Compare behavior with the retained controls; costs alone guide decisions.
Retain every attempt. No concurrent review scans, other tests or blueprint timing.
The profile launcher instruments execution and is separately hashed; unprofiled
CLI measurements use the source-bound successor directly.

Separately probe immutable blueprint sizes 0, 16, 128, 1024. Enumerate the first
N lexicographic pairs from the 52-card deck in one fixed six-player preflop state
(200 chips each, button 0, blinds 1/2). Every explicit action is CALL. The table
is synthetic and has no playing-strength meaning. Observe first hit, last hit,
and absent key (last deck pair), skipping hit cases for the empty table.
Through public action_for/propose, measure five batches of 20 calls after three
warmups. Record median and full batch values using perf_counter_ns. Separately
measure source digest cost and source/provider construction time. A separate
tracemalloc pass records retained and peak Python allocations from constructing
the source and its owned provider; it is not OS RSS or a process-tree memory bound.
Retain one 20-call profile at 1024 entries to attribute lookup cost. No strategy
change, index, cached digest, compiled dependency, or adaptive size selection.

Results support selecting the next bounded optimization. They do not establish
worst-case action latency, learned-table distributions, millions-entry scaling,
15-second search quality, or research evidentiary standing.
