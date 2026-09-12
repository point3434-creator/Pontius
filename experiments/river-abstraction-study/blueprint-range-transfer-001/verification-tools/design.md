# Blueprint range transfer 001

Question: does the frozen size-aware grouping repair remain useful on public ranges
conditioned on situations actually reached by the existing six-max checkpoint?

This is a four-case exploratory transfer pilot. It is not a six-max strength test,
a production resolver, or a test of the source node's real chip value.

## Population and inputs

Use baseline-000, iteration 76400, six players, 100 bb starting stacks, its exact bucket
artifacts, and purification threshold 0.05. Retain the first four eligible states from
seed 2026091207, at most 2000 hands. One state per hand, at the start of the river,
exactly two nonfolded players with positive stacks. The existing eligible predicate,
engine, policy and per-hand RNG define this. Complete each captured hand. No search
for favorable boards, no fallback filtering, no replacement after seeing ranges.
An incomplete capture or failed case withholds a complete-panel comparison.

The thin capture loop records the complete public action prefix plus replay deck,
board, seats, pot, stacks and commitments. The deck is replay evidence only. Build
public ranges by the existing public_range module. Replaying with different private
cards must reproduce both ranges. Folded players' action-conditioned card removal
is not jointly marginalized: this is a blueprint-factorized public-range model.

Retain every one of the 1081 board-legal holdings per role. Preserve raw weights,
floor at 1e-6 after normalization as the existing model specifies, and retain zeros,
collapse categories, floor applications, added mass and trained/uniform/miss/bad
provenance. Report the range L1 difference at floor 1e-9; do not rerun solves at it.
The joint model rejects only collisions and renormalizes; each holding has exactly
990 compatible opponents. No realized private cards restrict the public ranges.

## Comparison

Normalize all cases to pot 10, stacks 20, with check, half-pot bet 5 and pot bet 10.
After a bet the caller can fold or call. No raises or future street. Payoffs for the
bettor are check +/-5, fold +5, half-pot called +/-10 and pot called +/-15; ties zero.
All outcomes are enumerated, including exact ties. Source pots and stacks are metadata.

Apply the frozen witness-preference model and deterministic K=16 clustering separately
to both roles. No fitting or new hyperparameters. This also increases the population
from the earlier 96 hands per role to 1081: any transfer difference cannot be attributed
solely to range shape. It tests a harder compression ratio as well.

Train both incumbent roles for 50000 updates with the existing plain-regret learner.
Keep the caller fixed thereafter. Compute a fresh asymmetric witness and apply the
unchanged one-split/one-merge size-aware bettor repair. Train its bettor from zero
for 50000 updates. Accept exactly when its full-combo security is no worse than the
incumbent; otherwise retain the incumbent. No epsilon, rounded comparison or tuning.

Control: reconstruct the incumbent bettor learner, verify its 50000-update average
exactly, and continue in blocks of 250 updates. Stop at the first block whose measured
incremental time covers the repair's witness, proposal, setup, updates and average.
The reconstruction is audit overhead, not new decision-time work. Stop incomplete
if 1000000 additional updates cannot cover that budget. Record every block endpoint
and overshoot. Apply the same exact acceptance gate to continuation.

Report unchanged, selected repair and selected continuation exploitability per case
and equal-weight mean. Report both gate costs and total component times separately;
time matching excludes gates. Repair runs first because its measured cost sets the
control budget; this one timing observation does not establish a stable speed ratio.
Keep even rejected proposals and worse raw candidates. Report the original and proposed
grouping floor intervals to separate representational loss from unfinished optimization.
The unrestricted response evaluator visits every hand, not sampled deals.

## Numerical and execution boundaries

Use existing LP and learner code unchanged. Certify both asymmetric LP pairs against
the exact rational values of the full binary64 payoff coefficients, gap at most 1e-8.
These are exact certificates for that matrix, not for unrounded real-valued ranges.
The new integer aggregation adapter preserves every coefficient without rounded group
sums. Verify it against the literal Fraction evaluator, every full matrix coefficient,
and twelve literal subgame comparisons. Recheck all certificates without new LP calls.

One worker, one BLAS thread, Python 3.14.6, existing phevaluator CPython 3.14 extension.
No dependency installation. Native ranks checked against the independent Python
evaluator, including ties. No tracemalloc during timings. Timeout 1800 seconds each
for worker and verification; no hard RSS cap. Sequential four full-combo cases.
Synthetic full-size preflight precedes capture and computes no research outcomes.

Freeze source, design, runtime, model, checkpoint and previous milestone pins before
capture. Replay capture, range construction, private-card invariance and all learner
updates in a fresh verification process. Retain results, failures and non-improvements
under a new named milestone. Preserve previous milestones and existing dirty files.
No training checkpoint update, live bot invocation, commit or push.

Four reached states cannot establish generalization across boards, checkpoints or
six-max opponents. This pilot decides whether a larger, more representative transfer
test is worth considering; it does not promote the repair into a playing policy.
