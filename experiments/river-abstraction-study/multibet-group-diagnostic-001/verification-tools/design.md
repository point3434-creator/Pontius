# Multiple bet sizes: representation diagnostic 001

Question: do existing learned hand groups hide useful bet-size distinctions when
check, half-pot and pot-sized bets coexist? No repair adaptation or acceptance gate.

Eight known cases: board indices 0, 4, 8, 12 from the retained 16-board group-repair
confirmation, each in uniform and polarized regimes. These are the first board in
each declared texture stratum. No fresh-board claim. Pool 0, 96 hands per role,
pot 10, stacks 20. Use the frozen preference model and its half-pot-derived K=16
partition for all menus. Partition stays fixed; the number of action probabilities
necessarily grows with the menu. Caller has separate call probabilities after each
observed bet size. No raises or subsequent streets.

Menus: check/half-pot; check/pot; check/half-pot/pot. Reconstruct each one-bet game's
payoffs from the existing constructor; require identical deals, check payoffs and
fold payoffs before combining. Never let the caller conflate the observed sizes.

For every menu, solve two asymmetric games (restricted bettor/full-hand caller and
full-hand bettor/restricted caller) plus a full-hand reference. Solve both opposing
LPs for each and certify their original-payoff saddle intervals within 1e-8 chips.
The grouping floor is the difference of asymmetric values divided by two.
Binary64 payoff values are interpreted exactly; bettor probability weights are
normalized using Fractions, caller probabilities remain binary64 interpreted exactly.

Train independent role regret learners against full-hand responses to 10k and 50k
updates. Retain exact exploitability, policies, setup and active times. These are
fixed-update convergence diagnostics, not equal-compute or live-latency comparisons.
Replay all saved endpoints without LP solving in a separate verifier.

For the combined menu, inspect its restricted-bettor opponent witness. Compute the
fixed-witness gain from allowing hand-specific size selection while retaining one
shared group betting probability. Count groups containing strictly half-pot-preferring
and strictly pot-preferring hands (1e-10 weighted payoff margin). Positive gain is
evidence of hidden size distinctions under that witness; zero is inconclusive because
other optimal witnesses may differ. It does not prove a proposed repair will succeed.

Descriptive decision criteria: combined-menu mean grouping floor >1e-6 chips, and
size-selection gain >1e-6 in at least four of eight cases. Report all failures,
per-case values, per-role losses relative to full-hand value, and residual training
gaps. This diagnostic ends with whether size-aware repair is worth investigating;
no repair implementation is included or implied by a positive result.

Five analytic tests include observed-size separation, a known size-conflict floor,
exhaustive pure-response enumeration, one-bet legacy solver/trainer equivalence and
invalid-policy refusal. Python 3.14.6 only, one BLAS thread, no allocation tracing.
900-second worker/verifier limits; each LP 10 seconds and 20k iterations. No hard RSS
cap. Freeze source, inputs and design before evaluating these menus. No automatic
retry or missing-case deletion; retain failures. No source adoption, commit or push.
