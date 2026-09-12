# Fixed-group regret variants 001

Question: do two fixed regret-update recipes reach the same certified group-limited quality
faster than the current independent-role learner against unrestricted best responses?

Controller: "Thanks for looking. Let's move on to the next research then."
Scope is a bounded development experiment, not production adoption or publication.

Reuse all 16 incumbent cases from multibet-size-confirmation-001, in their retained order.
These are now known development inputs: eight boards, four textures, two range regimes.
Keep K=16, holdings, weights, payoffs, action menu, and role-specific full-hand responses fixed.
Train both roles from zero. Do not run grouping repair or select cases by previous outcomes.

Arms:
- rm: cumulative signed regrets and uniform average, reproducing the frozen learner.
- rm_plus: clip cumulative regrets to zero AFTER adding instantaneous regret; t^2 averaging.
- discounted: after adding regret at one-based t, multiply positive totals by
  t^(3/2)/(t^(3/2)+1), nonpositive totals by 1/2; t^2 averaging.

The weighted sums implement the quadratic output weighting directly. They are not a change
to reach weighting: each role's reduced one-decision game is unchanged. Recipes follow the
quadratically weighted RM+ comparator and default (alpha,beta,gamma)=(1.5,0,2) in Brown and
Sandholm, https://arxiv.org/pdf/1809.04040, pp. 3-4. These are empirical adaptations to our
best-response schedule; do not claim a full CFR implementation or inherited convergence rate.
Recipes bundle regret and averaging choices; this run cannot attribute effects to one alone.

Checkpoints: 500, 2000, 10000, 25000, 50000. Two timed repetitions, rotating arm order by case
and reversing it on the second repetition. Second-repetition policies must match exactly.
Time includes setup, updates and materializing each average; allocation tracing is forbidden.
Exact scoring is timed separately on the first repetition. Report both solver-only time and
first-pass time including cumulative checkpoint scoring. No claim of constant-time monitoring.

Reuse and reverify both asymmetric certificates on original coefficients. If E is exact
profile exploitability and [L,U] is the certified grouping-floor interval, remaining error is
[E-U,E-L]. A checkpoint passes epsilon only when E-L <= epsilon. Primary epsilon is 0.001
chip; secondary is 0.0001. Report first crossing AND the first sampled crossing whose later
checkpoints all pass; neither establishes behavior between checkpoints or after 50000.
Report failures to cross as censored; never drop them from time comparisons.
Report fixed-work residual curves and latest completed checkpoints within solver budgets
0.1, 0.5, 1, 2 and 4 seconds; no interpolation and no retrospective best checkpoint selection.
Timing uses both samples, reports their range, and is not a confidence interval.

Decision: a candidate earns fresh-board confirmation if it reaches the primary threshold
in all cases, has lower median paired persistent-crossing solver time, and improves that time
on at least 12/16 cases, without worse mean final residual than control. Otherwise preserve
the result and diagnose only a distinct mechanism; no parameter sweep or automatic extension.

Verification: analytic updates (sign changes and time indexing), direct weighted-average
check, legacy identity, small-game convergence, historical 50k checkpoint equality,
full replay using the frozen payoff update with separately implemented transforms,
exact certificate and profile re-evaluation, complete case/checkpoint census, immutable pins.
One worker, one BLAS thread, Python 3.14.6; 900 seconds per worker/verifier phase.
No hard RSS cap; these fixed tiny matrices have already run within prior development limits.
No live bot invocation, new LP solve, source-module change, commit or push.
