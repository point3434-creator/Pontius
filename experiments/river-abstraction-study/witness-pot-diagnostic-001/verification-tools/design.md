# Pot-sized failure diagnostic: witness-pot-diagnostic-001

User authorization: "Let's move on design and run please" refers to the proposed
diagnostic separating pot-sized solver and grouping failures. No commit, push,
production change or classifier fitting. Preserve fifteen earlier milestones.

## Fixed panels

Use the union of the two previously identified failure panels in bet-transfer-001:
all 48 polarized cases and all 24 multiple-pairs-or-trips cases, with 12 shared.
Thus 60 unique cases are run, not selected by individual score. Polarized means
give each of 16 boards equal weight; paired/trips means give each of four boards
equal weight. Report the panels separately, never use a pooled 60-case primary.
This is a post-finding diagnostic on observed cases, not a fresh confirmation.
All target games have pot 10, bet 10, stacks 20/20, 96 holdings per seat and one bet.

## Solver intervention

Two fixed representations: ordinary-preference and range-response. Compare the
existing alternating vanilla CFR with two independent regret learners, each
constrained to its own groups and opposed by an unrestricted exact best response
to its current policy. Pair the two average learner policies for evaluation.
This is the full-enumeration one-bet specialization of the CFR-BR principle from
Johanson et al., AAAI 2012. No sampling or multiplayer guarantee is involved.
Source: https://johanson.ca/publications/poker/2012-aaai-cfr-br/2012-aaai-cfr-br.pdf

Initialize zero regrets and uniform policies. One iteration updates each seat once;
best-response ties choose probability 0.5. Use unweighted average policies. Save
1000, 10000 and 50000 iterations for both algorithms. New ordinary-CFR checkpoints
at 1000/10000 must reproduce the retained baseline exactly. Order rotates across
the four algorithm/representation combinations by case index. Iterations match,
but per-iteration arithmetic differs: times are diagnostics, not equal-time or
speedup claims. Model coefficients and the two group assignments remain frozen.

Primary solver flag: mean learned-BR minus learned-CFR full-hand exploitability
below -1e-10 chips at 50000 iterations in the polarized panel. Separate ranking
repair flag: learned-BR beats response-BR there at the same checkpoint. Report
1000/10000 checkpoints, both panels, the intersection, board means and omitted-board
means regardless of flags. Measure residual above each existing certified floor.
Pair the retained constrained-seat LP policies as 120 oracle strategy targets;
their full-hand exploitability must equal the upper floor certificate endpoint.

## Grouping intervention

On the 24 paired/trips cases only, construct two additional oracle-assisted group
pairs. Each uses three retained unrestricted opponent witnesses, in fixed order:
ordinary-preference, range-response, range-equity. For each seat the opponent is
the unrestricted witness from that seat's constrained LP. Derive the existing
conditional action-advantage features, clip every coordinate to [-0.5,0.5], then
use existing weighted anchored_clusters at the exact frozen occupied capacity.

half_witness uses both half-pot payoffs and half-pot witnesses. pot_witness uses
both pot-sized payoffs and pot-sized witnesses. Evaluate both groupings' certified
floors on the pot-sized game. This changes payoff AND opponent-witness context;
it is not an ablation of a single scalar input. Both variants have three columns,
the same clipping rule, clustering algorithm, weights and group counts. No sweep,
selection of the better variant, retraining or new CFR run on these groups.

These variants consume target-case oracle information and are NOT deployable
learned candidates or generalization evidence. They test whether same-capacity
regrouping with exact signals can address the observed limitation, and whether
updating context helps beyond half-pot exact signals.

Grouping repair flag: pot_witness mean floor upper difference is negative against
BOTH frozen learned and response floors on the paired/trips panel. Separate
context-gain flag: pot_witness beats half_witness by the same interval rule.
Report all variants, boards, regimes and omitted-board panels without substitution.
No combined pass/fail averaging across the solver and grouping interventions.

## Execution and evidence

240 new solver trajectories (60 cases x two solvers x two representations),
720 saved checkpoint policies, 120 retained LP strategy targets. 48 oracle group
pairs (24 cases x two contexts) require exactly 96 new LP calls. Existing per-LP
limits stay five seconds and 10000 iterations with rational certificate checks.
Worker and verifier each have a 1200-second timeout; no RSS cap or peak-memory
claim. Python 3.14.6, NumPy 2.5.2, SciPy 1.18.0, one BLAS thread, no tracemalloc.

Test first: retain the non-updating RED scaffold and its failing analytic update
test, then verify GREEN against scalar trajectories, exhaustive pure responses,
a known optimal grouping floor, zero-payoff ties and invalid-input controls.
Check witness feature arithmetic, clipping and occupied-capacity preservation.
Run the existing CFR/certificate tests. No scored-panel rehearsal.

Freeze design, scripts, model, complete predecessor manifests and transitive pins
before any retained scoring. Refuse an existing output root. Parent reconstructs
the 60 games, verifies 360 retained pot certificates plus 144 half-pot certificates
and 96 new oracle certificates: 600 certificates total, with LP disabled. Replay
all solver policies from scratch (12 million paired update iterations); scalar
fsum independently checks full-hand values/BRs and the 120 LP targets. Rebuild
oracle features and labels, verify the half/pot context bindings, and independently
recompute summary means, rational intervals, differences and all four flags.
Retain raw policies, intervals, failed outputs if any, scripts, receipts and report.
