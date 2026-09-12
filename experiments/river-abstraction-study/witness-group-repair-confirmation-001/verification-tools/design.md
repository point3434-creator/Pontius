# Frozen fresh-board confirmation of one-step witness repair

Request: "lets confirm run on fresh boards". This authorizes this bounded research
run. It does not authorize adoption, commit, push, or production play.

Sixteen fresh boards, four in each existing texture stratum. Deterministic
hash-shuffled decks use seed witness-group-repair-confirmation-001. Exclude every
five-card board occurring in the 21 retained historical plans, their training
and exclusion lists, and the library development/holdout lists, up to all 24 suit
permutations. Select before scoring. Retain the exclusion inventory and attempts.
This deliberately stratified panel does not estimate natural board frequencies.

Unchanged: ordinary-preference frozen model, eleven raw features and 78-column
design; 16 occupied groups per seat; 96 holdings per seat; pool 0; uniform and
polarized ranges; pot 10; stacks 20/20; bets 5 and 10. Thus 64 paired cases.
Use the exact original deterministic hand-pool rule. No model fit or tuning.

Unchanged repair: independently for each seat, one mixed-sign witness-advantage
group is split, with zero on the nonpositive side; merge two other original
groups. Choose maximum strictly positive exact fixed-witness gain minus merge
cost, tie-breaking by ascending split/merge labels. Otherwise no-op. Retain all
proposals including regressions. Do not select using the repaired certificate.

Generate the baseline witness separately for each new case. This is offline
game-specific refinement, not unaided model generalization. Reuse unchanged
frozen repair and numerical helpers by explicit file imports. Build the baseline
and repaired certificates (256 LP calls total). Start both solvers from uniform.
Control checkpoints: 10,000 and 50,000; repaired: 1,000 and 10,000. No early stop.
There are 128 trajectories and 3,840,000 updates per full replay. Separate
preparation, baseline witness, proposal, repaired LP, and solver timings.
The 50k comparison is an iteration-budget comparison, not equal total compute.

Half-pot remains primary. Representation support: the upper endpoint of the
equal-weight mean repaired-minus-original certified floor difference is below
-1e-8 chips. Practical support additionally requires mean repaired10k minus
original10k below -1e-6 chips. Preserve these pilot criteria unchanged. Report
both bets, all board means, textures, regimes, leave-one-board-out means,
individual floor directions and worst regressions. These are descriptive
thresholds, not confidence bounds on unseen boards. Sixteen board units, not
64 independent boards. No claim of six-max, full-range or BB/100 strength.

Reconstruct every input and baseline group. Verify all 256 asymmetric
certificates and 256 profiles with LP calls forbidden, replay every trajectory,
and independently enumerate all permitted partitions for each repair. Recompute
every summary using rational arithmetic outside the summary helper.

Python 3.14.6, NumPy 2.5.2, SciPy 1.18.0, one BLAS thread, no allocation tracing.
900-second timeout per sequential worker/verifier phase; no hard memory cap.
Claim the output with exclusive directory creation; capture failures, no retry
or seed replacement. Preserve all 21 prior milestones. Retain a named immutable
milestone even for a negative result. No source edits or cold-review claim.
