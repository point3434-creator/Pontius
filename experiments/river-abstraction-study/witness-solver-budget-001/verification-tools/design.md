# Frozen solver-budget experiment: witness-solver-budget-001

The user authorized design and execution: "Let's design and run the test".
This is the agreed test of actual solver usefulness for the frozen learned groups.
No commit, push, model adoption, production change or model fitting is authorized here.

## Question and population

Use every one of the 96 cases in witness-preference-confirmation-001: 16 observed
boards, three hand pools and two synthetic range regimes, 96 holdings per seat,
heads-up one-bet river, pot 10, bet 5, stacks 20/20. This is a solver benchmark on an
observed panel, not a new generalization sample. Preserve the entire population.
Ordinary-preference is frozen byte-for-byte. References are range-response and
range-equity. All three use the predecessor's matched occupied group counts.

## Solving and clocks

Use the existing alternating vanilla CFR, zero regrets, uniform initial policy,
unweighted average strategy, deterministic full-tree updates and no random seeds.
Separate iteration runs save 100, 1000 and 10000 iterations. Three independent
timed runs save policies at 0.05, 0.2 and 0.5 seconds. Each method starts over.
Method order rotates by case index for fixed work and by case index plus repetition
for timed work; every case sees every timed position once per method.

The timed boundary starts with a loaded exact payoff game, full-board equities and
loaded frozen model coefficients. It includes capacity derivation, method-specific
features, prediction where needed, clustering, payoff aggregation, CFR setup and
updates. Imports, common game/equity construction, certificates, file I/O and policy
evaluation are excluded. Report common construction separately; this is not cold
process or end-to-end live-poker latency. No tracemalloc; one BLAS thread.
The clock runs continuously during timed work, paused only while recording a
checkpoint. Copies preserving the pre-step strategy are charged to timed work.
At a budget boundary save the last fully completed iteration before that boundary,
not the first iteration after it. Retain its timestamp and the crossing timestamp.
If setup misses a budget, report the pre-existing uniform policy at iteration zero
and flag the miss; never drop that cell. A timed trajectory has a 100000-step safety
limit. Reaching it before the final deadline is a failed experiment, not a result.

## Endpoints and interpretation

Evaluate lifted policies against unrestricted full-hand best responses. Report
actual exploitability, restricted-game exploitability, individual deviation gains,
the retained certified grouping floor and actual-minus-floor residual. A compressed
equilibrium need not attain the best representable full-hand floor; do not equate
the residual solely with insufficient iterations.

Primary fixed-work endpoint: equal-board mean candidate-minus-range-response
exploitability at 10000 iterations. Primary time endpoint: the same difference at
0.5 seconds, averaged equally over three repetitions within each case. A numerical
improvement flag requires both differences below -1e-10 chips. Secondary checkpoints
and range-equity comparisons cannot replace failed primaries. Report each timed
repetition, all board/texture/regime means, leave-one-board-out means and worst cases.
Separate robustness flag: both primary differences are below -1e-10 in every
texture, regime and leave-one-board-out panel, and each timed repetition's primary
mean is below -1e-10. No formal confidence level, BB/100 or six-max claim.

## Bounds and verification

One retained worker, maximum 1200 seconds; parent verification has a separate
900-second subprocess limit. No RSS cap or peak-memory claim. Exactly 1152 CFR
trajectories and 3456 saved checkpoint policies if complete. No LP solves or fitting.
Refuse an existing output directory. Pin all predecessor members, transitive input
pins, experiment scripts and imported project sources before launch; verify again
afterwards. Python 3.14.6, NumPy 2.5.2 and SciPy 1.18.0.

Before freezing, run existing CFR/full-tree parity tests and synthetic deadline,
setup-miss, policy-domain, aggregation and scalar-payoff checks. No scored panel
rehearsal. Parent reconstructs every input and grouping, verifies all 576 reused
asymmetric certificates without solving, replays each case/method once through its
largest observed iteration and compares every saved policy exactly. Independently
recompute all full-hand metrics using scalar fsum arithmetic, check restricted
best-response inequalities and floor bounds, and derive all summary cells anew.
Retain raw policies, clocks, failed outputs if any, receipts, source and audit.
Preserve all thirteen previous milestones and unrelated worktree edits.
