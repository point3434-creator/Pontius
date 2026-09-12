# Magnitude-aware threshold preferences: witness-ordinal-001

Authorization: "Let's design and run it!" accepts the proposed multi-threshold,
bet-conditioned predictor test. Preserve seventeen earlier milestones. No production
change, adoption, commit or push. Fit and evaluate once under the frozen plan.

## Data and model

Reuse all 64 training cells and certified witnesses from bet-conditioned-001,
byte-preserving their original records. Eight original boards, two pools, two
regimes and bets 5/10; 96 holdings per seat, pot 10, stacks 20/20, one-bet heads-up.
No new training LP calls. The three witness columns remain old learned, response,
equity, in that order; conditional-own-hand action advantages stay unchanged.

Predict whether each advantage exceeds -0.25, 0, +0.25 chips. A computed equality
gets label 0.5. Witness-major, threshold-minor order gives nine outputs per seat.
These fixed cutoffs coarsely resolve the predecessor's [-0.5,0.5] clipping range.
No threshold search, normalized units, evaluation-based selection or adaptive retry.
The input remains eleven probability features plus bet/pot, with the same
91-column quadratic basis. Ordinary ridge-logistic objective, lambda 0.001 on
slopes only, marginal weights normalized to 1/64 per training cell. Use the sealed
fit procedure: zero initialization, gradient <=1e-8, at most 80 Newton iterations,
40 Armijo backtracks. Eighteen fits (twelve new threshold tasks and six zero tasks).
The six zero-threshold fit records must exactly reproduce the retained conditioned
model. The previous three-output conditioned model remains a frozen baseline.

Use all nine raw sigmoid outputs directly as clustering features. No isotonic
projection or sorting: these are independent preference predictions, not a claim
of a coherent cumulative distribution. Report marginal-weighted crossing frequency
per seat and witness (a later threshold exceeds an earlier one by >1e-12), but do
not select models or modify features based on it. This increases output count and
effective model parameters; equal group capacity is not equal model size or time.

## Untouched evaluation

Select eight new boards, two per texture, with frozen SHA-256 seed
witness-ordinal-001. Exclude all 44 previous boards and suit isomorphisms. Same two
pools and regimes at each of two bets: 64 cells, eight balanced board units. The
board list is frozen before training. Write/hash candidate before any evaluation
cell exists, then disable fitting. No learner receives holdout witness targets.

Compute certified floors for ordinal, previous sign-conditioned, old learned,
range-response, oracle-ordinal, oracle-sign and oracle-clipped groupings. The three
oracle controls use the same target-game witness bank; they compare coarse
magnitude labels, signs alone and clipped continuous advantages. They are not
deployable candidates or bounds over all possible partitions. Preserve the equity
bank certificate for provenance. Group counts and anchored clustering are unchanged.

The four non-oracle candidates use the same preserved RegretBR solver, starting
from zero, with checkpoints 1000/10000/50000, averaged policies and tie probability
0.5. Order rotates by case index. No sampling or equal-wall-time claim. Totals:
1024 new evaluation LP calls, 256 trajectories, 768 saved checkpoint policies.
Keep the prior five-second/10000-iteration LP limits and rational certificates.

## Frozen decisions

Primary actual flag: ordinal minus previous sign-conditioned mean exploitability
at 50000 iterations is below -1e-10 on pot-sized cells. Separate floor flag: upper
endpoint of mean certified floor difference is negative. Practical candidate flags
require the corresponding comparison to beat both old learned and range-response
on pot-sized cells. Cross-bet robustness requires actual and floor gains against
all three non-oracle references in every texture, regime and omitted-board panel
at both bet sizes. Report all checkpoints, cases, boards, oracle controls and
crossing diagnostics, regardless of flags. No pooled cross-bet primary mean.
Each bet's mean gives each of eight boards equal weight. No population confidence
claim; this is a small fresh-board pilot, not six-max strength or BB/100.

## Preflight and verification

First retain a failing boundary test against repeated zero-threshold labels. Then
test all scalar cutoffs/equalities, zero-head identities, crossing diagnostics,
invalid inputs, fresh-board disjointness, capacity and holdout-label independence.
Exercise the independent summary audit on a synthetic full-shaped panel. Recheck
the existing fit/data-boundary and best-response tests; no scored-panel rehearsal.

Freeze design, model code, inherited implementation and all input pins before run.
Python 3.14.6, NumPy 2.5.2, SciPy 1.18.0; one BLAS thread; no tracemalloc. Worker
and verifier each have a 1200-second limit. No RSS cap or peak-memory claim.
Refuse an existing output directory and retain any failure rather than overwrite.

Parent disables LP, reconstructs retained training games, verifies 384 training
certificates and 1024 fresh certificates (1408 total), and reproduces all 18 fits.
Then disable fitting, reconstruct all fresh predictions/groups, and require the
zero-threshold predictions to equal the sign-conditioned baseline on every hand.
Replay all 768 policies from zero (12.8 million iterations). Independent scalar
full-hand evaluation and Fraction summary checks cover scores, intervals, panels,
decisions and crossing frequencies. Retain all results and seventeen predecessors.
