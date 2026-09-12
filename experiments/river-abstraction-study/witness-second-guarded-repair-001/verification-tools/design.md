# Second guarded repair 001

User: "Let's build and run" approves the proposed small second-step test.
Use all 64 cases of witness-guarded-repair-confirmation-001, without filtering by
first-step gain: 16 boards, two range regimes, two bets, one 96-holding pool per
seat. This reuses known first-step outcomes. Second-step outcomes are unobserved
when frozen, but this is not a new-board replication or a population estimate.

Begin each case at the retained accepted first-step groups AND saved policy,
independently per seat. Do not restart from the unconditional repair proposal.
Reconstruct the original game and verify the retained policy. Recompute a fresh
asymmetric witness on the current groups and include its cost; do not reuse the
previous diagnostic candidate certificate for free.

Generate exactly one additional fixed-capacity split/merge per seat with the
unchanged frozen repair rule. Keep K=16. Train the proposed groups from uniform
for 1k and 10k checkpoints. Apply the unchanged exact per-role security gate
against the retained first-step policy. Invalid input stops the run.
Repaired LP certificates are generated afterward for analysis, never for gating.

Control: keep the accepted current groups and continue their deterministic
learners from 10k to 20k. Reconstruct those learners from uniform and require
exact reproduction of the retained mixed first-step policy at 10k before using
20k. This is valid because these two asymmetric regret learners are independent
per role. Apply the same security gate to the 20k strategy, against the same
first-step policy. Both alternatives therefore receive an additional 10k updates
per role, but repair additionally needs witness generation and regrouping.

Frozen criteria, evaluated on the full retained panel:
- Exact safety: both guarded alternatives never worsen the retained first step.
- Useful second step: safety and half-pot mean improvement below -1e-6 chips.
- Beyond continuation: safety and half-pot mean second-minus-guarded-continuation
  below -1e-6 chips. These are descriptive criteria, not confidence intervals.
Report both bets, all board and texture/regime means, leave-one-board-out means,
raw proposal regressions, accept/reject counts, and losses versus continuation.

Measure incremental second-step components: fresh witness, proposal, new10k
solver setup/updates, acceptance. For continuation measure only updates10k-to20k
and acceptance. Exclude reconstruction of the existing 10k state, input setup,
checkpoint scoring, diagnostic LP, serialization, and verification. Report these
as component sums, not independently timed production launches or equal-CPU arms.

Fresh verification rebuilds games, validates 64 incumbents, checks 256 new
asymmetric certificates and 256 saved profiles, replays 1,920,000 updates, and
independently audits both gates and their 128 selected profiles. LP solving is
disabled in the verifier. Independently enumerate each permitted repair exchange.
No model fitting, population filter, retry, adoption, commit or push.

Python 3.14.6, NumPy 2.5.2, SciPy 1.18.0; one BLAS thread, no allocation tracing.
900 seconds each for the sequential worker and verifier; no hard RSS cap.
Retain the complete outcome as a new milestone and preserve all 24 predecessors.
