# River time-budget quality 001

Question: does additional DCFR+ computation bought by graph replay reduce audited
strategy error within useful accounted time budgets?

This is a bounded extension of the retained graph experiment, with no production
changes and no new solver algorithm. Python 3.14.6 only. Reuse the frozen native
cuBLAS bridge and graph solver unchanged; its horizon parameter becomes 16,384.
The games, joint payoffs, ranges and released-code DCFR+ settings remain fixed.

Two expanded case-001 river trees; 1,081 hands per role. Checkpoints are 2,048,
4,096, 8,192 and 16,384 iterations. Three fresh trajectories per tree. Each starts
uniform, warms 32 iterations, resets, captures and starts from iteration zero.
The 2,048 policy must match the retained graph experiment byte-for-byte, guarding
against a horizon-extension or discount-index regression. Every checkpoint in
every repeat gets an independent rational best-response audit.

Time budgets are 3, 5, 10 and 15 seconds. Select the highest iteration count whose
charged cost fits; never inspect strategy error to select a checkpoint. Missing
coverage stays missing. Show all checkpoint errors, including regressions, and
compare selected error with that trajectory's fixed 2,048-iteration anchor.
This is not a new CPU-versus-GPU wall-time race or a claim about six-max strength.

Charged cost is observed worker time from launcher start through the checkpoint's
policy export (including preparation, prior checkpoint observation and float
scoring), plus unassigned process overhead, plus a separately executed fresh
exact-audit process. Unassigned overhead is max(0, parent-observed full worker
wall minus worker elapsed through close), charged conservatively to every prefix.
Audits of earlier checkpoints are research diagnostics and do not enter a later
checkpoint's cost; each counterfactual prefix includes its own audit. Report this
accounting sum explicitly. It is not an enforced live deadline, and different
hardware/load can change affordability. Do not choose the lowest-error observed
policy after seeing the outcomes, nor claim all repetitions fit from a median.

Bounded validation runs only the 2,048 checkpoint on both trees, using the full
16,384 horizon and exact audits. This validates the runner and anchor; it is not
the main experiment. The built campaign command exists but is not run as part of
the build request. Each worker has a 180 s timeout and a 3,072 MiB sampled private
memory stop; the campaign has a 600 s wall envelope. CuPy's pool is capped at
1,024 MiB, excluding allocations outside the allocator. CPU audit is separate.

Preserve the preflight and design with source/input digests. Do not create a new
completed research milestone or imply a quality finding before the full campaign.
No commit, push, policy adoption, or bot integration is included.
