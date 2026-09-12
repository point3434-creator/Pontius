# Seat crossover and range-shape diagnostic

Authority: "Can you design and run the next test?" One bounded diagnostic invocation.
No model fitting, optimization calls, new boards, policy adoption, commit or push.

Use all 48 already observed evaluation cases from witness-clipped-target-001 and
witness-boundary-001. Old means full-target quadratic predictor clipped afterward;
new means clipped-target quadratic predictor clipped afterward. Reuse group vectors
and seat witnesses unchanged. Four fixed arms are old_old, new_old, old_new, new_new,
with bettor (seat 0) first and caller (seat 1) second. No case-dependent selection.

For the fixed two-player zero-sum one-bet game, let a(G0)=max_XG0 min_Y V and
b(G1)=min_YG1 max_X V. The least full-hand profile exploitability representable by
the two groups is [b(G1)-a(G0)]/2. Each value depends on just one group vector.
Consequently old/new certificates can be crossed without solving again. This is not
an equilibrium claim for the doubly compressed game or a property of six-max poker.
Freshly reconstruct each payoff game and certify all four unique asymmetric witnesses
per case. Require equality with pinned exact-rational endpoints and gap <=1e-8.
Verify all crossed group capacities and identities; old_old/new_new must reproduce
the previous floor records exactly. A separate arithmetic audit checks crossed floors,
contrasts and aggregates directly against original certificates.

Primary endpoints: signed changes in floor caused by changing only the bettor or
only the caller, each against old_old, on the equal-board panel. Bettor change is
[a_old-a_new]/2; caller change is [b_new-b_old]/2. Negative favors the new model.
The both-seat effect is their sum algebraically; zero seat interaction follows from
the estimand and is not an empirical discovery about poker. Retain interval arithmetic
and shared-value cancellation rather than introduce false independent uncertainty.
Report all four arms against range_response, range_equity and clipped_oracle, full
board/pool/regime/texture results and leave-one-board-out sensitivity. No new winner
threshold. A favorable observed arm would still require reserved-board confirmation.

Range-shape question: pair uniform and polarized cases on each identical board/hand
pool (24 pairs). Report polarized-minus-uniform changes in each seat effect, with
equal board weighting and all pairs retained. This changes both players' range
weights and all their derived model/group inputs; it does not identify the effect
of polarizing either player alone. The existing synthetic polarized law multiplies
weights by four when uniform showdown equity <=.2 or >=.8; otherwise weight one.
Support remains the same. It is not a posterior range induced by prior betting.
Retain low/middle/high mass before and after collision conditioning for both seats
and regimes so that the label is tied to what the range generator actually does.

No inference of street progression, natural range reach probabilities, or fresh
generalization. Board and range comparisons are descriptive, not sampling confidence
intervals. All preidentified severe cases stay included. Prediction errors are not
used to choose an arm. Retain full outcomes including nonimprovements.

Execution: Python 3.14.6, NumPy 2.5.2, SciPy 1.18.0, one BLAS thread, 600-second
worker limit, parent verification outside it, no RSS cap. Exclusive output reservation,
checked subprocess exit/captures, immutable pins before and after, no automatic retry.
New optimization and fitting entry points are disabled and attempts cause failure.
Synthetic endpoint, sign, shared-value cancellation, feasibility and refusal checks
precede the bound invocation. Archive as witness-seat-crossover-001; preserve all ten
prior milestones and unrelated worktree changes.
