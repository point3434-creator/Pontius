# Bet-conditioned preference pilot: witness-bet-conditioned-001

Authorization: "Let's run it" accepts the proposed small bet-conditioned predictor
test on untouched boards with the same unrestricted-response solver for all learned
baselines. No production changes, adoption, commit or push. Preserve 16 milestones.

## Question and population

Does adding bet size help a preference predictor generalize to new boards, and does
it recover any of the target-game oracle grouping advantage? Use the original eight
training boards from preference-001, pools 0 and 1, both uniform and polarized ranges:
32 base cases at bets 5 and 10, or 64 training cells. Each has 96 holdings per seat.
Pot 10, stacks 20/20, heads-up one-bet games, built through the public RiverHoldem path.

Select eight new boards, two per declared texture, by fixed SHA-256 ordering seed
witness-bet-conditioned-001. Exclude every prior board and its suit isomorphisms from
the original development/holdout and preference-confirmation panels (36 boards).
Use the same two pools and regimes: 64 evaluation cells, eight board units, not 64
independent boards. Freeze selection and all implementation bytes before scoring.
Fit solely on training cells and write/hash the candidate before opening any
evaluation cell. No tuning, early stopping by evaluation loss or optional extension.

## Targets and matched ablation

On each training cell, solve the three fixed bank groupings in this order:
ordinary_preference (old frozen model), range_response, range_equity. The three
unrestricted opponent saddle witnesses give three conditional action advantages per
hand and seat. Class labels are 0 / 0.5 / 1 for negative / exact zero / positive.
Use separate bettor/caller logistic models with three outputs each.

conditioned receives eleven unchanged raw probability features plus bet/pot (0.5 or
1). blind receives identical features with that last coordinate masked to zero.
Both use the same 91-column quadratic expansion, data, own-hand marginal weights,
and ordinary cross-entropy objective. Normalize each training cell's seat mass to
1/64. Ridge 0.001 on slopes, unpenalized intercept; zero initialization, Newton at
most 80 iterations, infinity-norm gradient <=1e-8, 40 backtracks with Armijo 0.0001.
No cost weighting or new hyperparameter search. Twelve binary fits in total.
The blind ablation deliberately removes effective bet parameters, not training rows.

Three new output coordinates differ from the original four-output learned model;
therefore conditioned-versus-old is a whole-candidate comparison. Only conditioned
versus blind isolates exposing the bet input under identical targets and training.

## Evaluation

All methods use unchanged weighted anchored clustering with occupied group counts
matched to the original uniform-equity-200 capacity on each case/seat.
Compute certified grouping floors for conditioned, blind, old learned, response,
oracle_sign and oracle_clipped. The last two use exact target-game witness features:
three sign probabilities or three advantages clipped to [-0.5,0.5]. These oracle
controls are not deployable candidates and no learner consumes holdout witnesses.
The separate sign oracle reveals information loss from the chosen training target.
The bank's range-equity certificate is retained for target provenance, not a primary
comparison. Exactly 384 training plus 896 evaluation LP calls = 1280 total; existing
five-second / 10000-iteration LP bounds and rational saddle certificates unchanged.

For the four non-oracle groupings, run the preserved RegretBR solver from zero at
1000/10000/50000 iterations, no sampling, unweighted averaged policies, ties 0.5.
256 trajectories / 768 policies; order rotates by base-case index. Equal iterations,
not equal wall time or arithmetic work. Report full-hand exploitability and floors.

## Frozen decisions

Primary context test: on pot-sized evaluation cells, conditioned minus blind mean
actual exploitability at 50000 is below -1e-10. Separate floor flag: negative upper
endpoint of the conditioned-minus-blind certified interval mean.
Practical candidate flags: the same actual/floor rules beat BOTH old learned and
range-response on pot-sized cells. Report actual and floor flags separately.
Cross-bet robustness requires both measures to beat all three non-oracle controls
in every texture, regime and leave-one-board-out panel at both bet sizes.
Report every checkpoint, board, comparison and oracle even when a flag fails.
No pooling of half-pot and pot-sized games to pass the primary rules. Each bet's
means give eight boards equal weight. These are descriptive fixed-stratum results,
with no population confidence interval or six-max/BB-per-100 claim.

## Checks, execution and retention

The bet-input test first fails against a bet-blind RED scaffold. GREEN checks toy
conditional learning, analytic constants/ties, weight scaling, finite-difference
gradients and invalid inputs. Add public-game/feature/capacity/disjointness checks
before freezing, with no scored-panel rehearsal. Python 3.14.6, NumPy 2.5.2, SciPy
1.18.0, one BLAS thread, no tracemalloc. Worker and verifier each limited to 1200s;
no RSS ceiling or peak-memory claim. Refuse an existing output root.

Parent verification disables LP, rebuilds training targets, checks all 1280
certificates, refits all 12 training tasks exactly, verifies candidate provenance,
then disables fitting and reconstructs fresh-board predictions/groups. Replay all
768 policies from zero (12.8 million iterations). Independent scalar arithmetic
checks full-hand scores; independent Fraction arithmetic rebuilds every summary.
Confirm blind features/groupings identical across bet sizes. Preserve all training
rows, witnesses, model coefficients, oracle controls, failures, scripts and receipts.
