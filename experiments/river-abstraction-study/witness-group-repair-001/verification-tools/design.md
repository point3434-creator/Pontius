# Witness group repair 001

The user requested a next experiment and explicitly said to build and run it.
Freeze before scoring; one retained invocation and verifier, no automatic retry.

Question: can one witness-directed split/merge improve a learned hard partition
at fixed capacity? This is case-specific offline abstraction refinement. It uses
a previously solved witness from the evaluation game itself. It is not a new
learned model, an unseen-board generalization test, or a cheap inference method.

Keep every K=16 hard baseline from soft-assignment-001: eight observed boards,
pool 0, uniform/polarized ranges, bets 5/10, pot 10, stacks 20/20, 96 hands per
seat. There are 32 paired cases. No selection by score or texture. All prior
models, features, group labels, certificates and saved policies are frozen.

For each seat independently, take the unrestricted opponent witness from its
retained asymmetric LP. Compute each own hand's joint-mass-weighted action-1
minus action-0 payoff against that witness using exact rational arithmetic on
the original binary64 coefficients and witness. Caller utility reverses the
payoff sign and includes opponent betting reach. No marginal reweighting.

Enumerate a single allowed exchange. Split an occupied group with both positive
and negative advantages by sign: positive versus nonpositive (zeros on the
nonpositive side). Merge two other occupied groups, excluding both children
of the split. Capacity stays exactly 16. The split gain is min(total positive
advantage, absolute total negative advantage). If group totals are A and B,
merge cost is max(0,A)+max(0,B)-max(0,A+B). Choose the largest split gain minus
merge cost over all such exchanges; exact ties use (split, merge-a, merge-b)
in ascending order. If no positive-net exchange exists, preserve the partition.
This maximizes response improvement to one fixed witness within this exchange
family. It does NOT prove improvement after the opponent changes its response.

Evaluate every proposal unconditionally, including regressions and no-ops.
Do not use its new certificate to select a favorable proposal or discard a case.
Two new asymmetric LPs per case: exactly 64 calls with the existing 5-second /
10,000-iteration bounds. Original-game exact certificates must have gaps <=1e-8.
No new witness bank, fitted coefficients, feature changes or repeated refinement.

Primary: half-pot mean proposed-minus-baseline certified floor upper endpoint
< -1e-8 chips. Practical support additionally requires the proposal at 10,000
updates to beat baseline at 10,000 by more than 1e-6 chips in the mean.
Pot-sized comparisons and every board, texture, regime and leave-one-board-out
panel are secondary, reported without selecting a winner. These are descriptive
mechanism gates, not statistical significance or population confidence claims.

Run the proposal from uniform initialization for 10,000 RegretBR updates with
1,000/10,000 checkpoints. Run the original hard grouping from zero for 50,000
updates with 10,000/50,000 checkpoints. The 10,000 checkpoint must reproduce its
retained predecessor component policy exactly. There are 64 trajectories,
1,920,000 updates and 128 saved profiles. The control tests whether five times
the solver updates beat repair; it is not an equal-wall-time comparison. Retain
proposal construction, new LP, preparation and training times separately. Prior
LP/model creation costs remain outside these incremental timings, explicitly.

Verify all baseline and proposed certificates (128 asymmetric certificates),
all 128 profiles, and replay both trajectories in a separate process with LP
calls disabled. Recompute signs, all exchanges and selected operation. An
independent enumerator must confirm the selected fixed-witness objective by
summing optimized group actions directly, without the gain/cost shortcut.
Scores use original exact-hand best responses, with rational and independent
scalar evaluation agreeing within 1e-10 chips. Reconstruct from frozen ranges
and verify original provenance, hand ordering and joint probabilities.

Required synthetic tests: seat signs/reach, exact split/merge objective against
enumerated group action policies, known restriction-cost repair, no-conflict
and zero cases, insufficient capacity, preserved K, invalid witness rejection,
deterministic ties/zero assignment, runner refusal and replay checks. Rehearsal
uses synthetic data only. No observed case is scored before freeze.

Python 3.14.6, NumPy 2.5.2, SciPy 1.18.0; one BLAS thread, tracing disabled.
Worker and verifier each have a 900-second timeout. No hard RSS cap or memory
claim. Unique output, complete captures, failed runs retained, source/input
pins checked before and after, immutable evidence and report for any outcome.
All previous milestones remain unchanged; no production source modification,
adoption, commit, push or independent cold-review claim.
