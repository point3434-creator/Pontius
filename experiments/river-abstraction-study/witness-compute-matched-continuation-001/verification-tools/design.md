# Compute-matched continuation 001

Question: does the second guarded repair retain its advantage when unchanged-group
training gets its measured computation allowance? All 64 cases from the second
repair are included: 16 existing boards, two regimes, two bets. No fresh boards.

The incumbent is each accepted first repair. Reconstruct its independent per-role
learners from uniform to 10,000 updates and require exact coefficient identity.
This reconstruction is excluded from incremental cost. No new fitting or LP solve.

Reference work is the retained second repair's witness LP, proposal, training setup
and 10,000 updates. Reference total adds its security gate. Exclude diagnostic LPs,
input reconstruction, scoring, serialization and independent verification.

Continue a single deterministic trajectory in blocks of 100 updates. Time each
block, including its initial sums snapshot, without allocation tracing. Save the
last completed block before crossing reference work as matched. Save the first
block at or beyond reference total as generous. Limit total iterations to 200,000;
failure to reach the budget fails the run. No partial population or automatic retry.

Apply the unchanged exact per-role security gate to both checkpoints. Matched is a
nominal component-budget comparison: measured gate time can differ from historical
gate time. Report actual component ratios and ranges. Generous gives training the
entire reference budget and adds its gate on top, intentionally favoring continuation.
Do not call either an exact contemporaneous wall-time comparison. One timing pass;
saved iteration endpoints can be replayed, hardware timing cannot be reproduced.

Verify every retained incumbent-group asymmetric certificate and its lower bound
on achievable exploitability. Count repair profiles below that bound by more than
1e-8 chips. This addresses representation limits separately from convergence.

Primary descriptive criteria: both gated continuations nonworse than incumbent;
half-pot repair mean beats each continuation by more than 1e-6 chips. Report both
bets, case directions, boards, textures, regimes and leave-one-board-out means.
These are fixed-panel comparisons, not population confidence intervals.

Run worker and separate replay verifier, each bounded by 900 seconds. Python 3.14.6,
one BLAS thread, no hard RSS cap. Retain failures and successes as immutable named
milestones. This user-approved local run does not authorize adoption, commit or push.
