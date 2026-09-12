# Action-preference learning: witness-preference-001

## Result and research decision

Ordinary action-preference classification is a promising learned representation on
this observed panel. Its mean grouping floor is 30.65% below range-response, with
39 cases lower, eight higher and one overlapping. All eight board means improve,
and every leave-one-board-out mean remains favorable. It also outperforms the
previous mixed-model candidate in mean. Both seats contribute similar mean gains
against range-response. This merits freezing a candidate for fresh-board confirmation;
it is not confirmation already obtained or permission to adopt a playing policy.

The primary weighting hypothesis is not supported here: cost-weighted classification
has a 13.42% higher mean floor than ordinary classification (22 lower cases, 23 higher,
three overlapping). It is nevertheless 21.35% below range-response. Weighting helps
the caller but hurts the bettor more. Removing board 7 narrowly reverses the mean
weighted-versus-ordinary comparison; that board is retained in every main result.
This finding applies to the specified weighting rule and model, not every form of
decision-focused learning. No parameter was tuned after examining these outcomes.

Exact teacher preferences beat range-response in mean but are markedly worse than
clipped exact advantage features. Sign information is useful, but this representation
discards magnitude. The exact-preference arm is a privileged reference, not a bound
on learned grouping quality: learned probabilities are continuous, the teacher is
hard 0/1/.5, and clustering is not globally optimal. Ordinary classification beats
the exact-preference grouping in nine cases. That does not contradict its identity.

## Fixed design

Original 48 training cases; all 48 already observed evaluation cases, eight boards
x three pools x two range regimes, with 96 holdings per seat. No new boards, case
selection, hyperparameter sweep or control re-solving. The learned variants use
the same eleven inputs and 78-column quadratic basis, four sigmoid outputs per
seat, lambda=.001 and unpenalized intercept. Their outputs feed unchanged anchored
clustering with the original occupied capacities. Exact teacher preferences use
one for positive advantage, zero for negative and .5 for an exact tie. All three
arms are evaluated through 288 new asymmetric LP calls.

Both classifiers minimize binary cross entropy plus lambda/2 times squared slopes.
Ordinary loss uses normalized own-hand mass and equal base case weights. Weighted
loss multiplies that mass by absolute FULL, UNCLIPPED witness advantage, then
normalizes globally per output using training data only. This intentionally shifts
effective weight toward costly cases/hands; it is part of the intervention. The
normalization keeps total loss mass comparable between the two objectives. Ties
have zero cost weight. All 16 fitted outputs were nonconstant and converged.
Models were persisted before any evaluation-case calculation. The parent refit
all four seat models and reproduced their records exactly. No deployed source changed.

## Mean grouping floors

Lower is better. These are interval midpoints for the best full-hand profile
exploitability representable by the groups in the fixed two-player one-bet river
game, in conditional game chips. They are not win rates or BB/100. Eight boards
receive equal weight, each averaging the six declared pool/regime combinations.

| Representation | Mean floor |
|---|---:|
| clipped_oracle | 0.0004702769 |
| exact_preference | 0.0025282947 |
| new_new | 0.0057849204 |
| new_old | 0.0050053591 |
| old_new | 0.0068383031 |
| old_old | 0.0060587418 |
| ordinary_preference | 0.0035584041 |
| range_equity | 0.0057369186 |
| range_response | 0.0051313371 |
| weighted_preference | 0.0040359424 |

Crossover control names old_old/new_old/old_new/new_new refer to the preceding
full-target versus clipped-target regressors, bettor first and caller second. They
are frozen controls, distinct from the new preference classifiers.

## Paired comparisons

Delta is candidate minus reference. Counts are lower / higher / overlapping.

| Candidate | Reference | Mean delta | Counts |
|---|---|---:|---:|
| exact_preference | ordinary_preference | -0.0010301094 | 39/9/0 |
| exact_preference | range_response | -0.0026030424 | 42/6/0 |
| exact_preference | new_old | -0.0024770645 | 38/9/1 |
| exact_preference | clipped_oracle | 0.0020580177 | 6/31/11 |
| ordinary_preference | range_response | -0.0015729330 | 39/8/1 |
| ordinary_preference | new_old | -0.0014469551 | 29/18/1 |
| ordinary_preference | exact_preference | 0.0010301094 | 9/39/0 |
| ordinary_preference | clipped_oracle | 0.0030881271 | 0/48/0 |
| weighted_preference | ordinary_preference | 0.0004775383 | 22/23/3 |
| weighted_preference | range_response | -0.0010953947 | 38/9/1 |
| weighted_preference | new_old | -0.0009694168 | 29/18/1 |
| weighted_preference | exact_preference | 0.0015076477 | 10/38/0 |
| weighted_preference | clipped_oracle | 0.0035656654 | 0/48/0 |

All remaining comparisons are retained in summary.json.

## Seat contributions

The first three contrasts are against range-response. The last isolates weighting.
Negative favors the candidate. Contributions add algebraically for this estimand.

| Contrast | Bettor delta | Bettor counts | Caller delta | Caller counts |
|---|---:|---:|---:|---:|
| exact_preference | -0.0013694411 | 37/5/6 | -0.0012336014 | 41/7/0 |
| ordinary_preference | -0.0007764665 | 33/6/9 | -0.0007964665 | 34/12/2 |
| weighted_minus_ordinary | 0.0007512868 | 8/21/19 | -0.0002737485 | 30/15/3 |
| weighted_preference | -0.0000251797 | 23/16/9 | -0.0010702151 | 37/8/3 |

## Board and range results

| Board | Ordinary preference | Weighted preference | Exact preference | Range-response |
|---|---:|---:|---:|---:|
| 0 | 0.001639798 | 0.001566519 | 0.003091787 | 0.003241754 |
| 1 | 0.001503118 | 0.002093195 | 0.000653710 | 0.003078214 |
| 2 | 0.001388332 | 0.000998867 | 0.000234618 | 0.001571476 |
| 3 | 0.001825216 | 0.001755372 | 0.001004213 | 0.003067695 |
| 4 | 0.006920709 | 0.006574119 | 0.003484718 | 0.008928619 |
| 5 | 0.003051278 | 0.002834635 | 0.000897876 | 0.003562535 |
| 6 | 0.006374313 | 0.006557379 | 0.006229431 | 0.008947529 |
| 7 | 0.005764469 | 0.009907453 | 0.004630003 | 0.008652874 |

| Regime | Ordinary preference | Weighted preference | Exact preference | Range-response |
|---|---:|---:|---:|---:|
| polarized | 0.003275056 | 0.004313600 | 0.002480120 | 0.004064202 |
| uniform | 0.003841752 | 0.003758284 | 0.002576469 | 0.006198472 |

Ordinary classification improves both regime means. Weighted classification is
slightly better than ordinary on uniform ranges, worse on polarized ranges and
worse than range-response on polarized ranges. The synthetic range intervention
still reweights both seats at once; it is not a posterior induced by earlier betting.

| Omitted board | Ordinary minus response | Weighted minus response | Weighted minus ordinary |
|---|---:|---:|---:|
| 0 | -0.0015687868 | -0.0010125604 | 0.0005562265 |
| 1 | -0.0015726241 | -0.0011111627 | 0.0004614614 |
| 2 | -0.0017714743 | -0.0011700783 | 0.0006013960 |
| 3 | -0.0016201407 | -0.0010644049 | 0.0005557358 |
| 4 | -0.0015107935 | -0.0009155227 | 0.0005952709 |
| 5 | -0.0017246010 | -0.0011478939 | 0.0005767070 |
| 6 | -0.0014300355 | -0.0009104297 | 0.0005196058 |
| 7 | -0.0013850084 | -0.0014311052 | -0.0000460968 |

These are descriptive sensitivity checks, not confidence intervals.

## Preidentified difficult cases

| Case | Ordinary | Weighted | Exact preference | Range-response |
|---|---:|---:|---:|---:|
| b07-p1-polarized | 0.005446100 | 0.006211555 | 0.002903252 | 0.010144316 |
| b07-p2-polarized | 0.004525777 | 0.018815445 | 0.000518106 | 0.008609137 |

Both cases use 6h 6s Jh Qc Qd and polarized ranges. Neither is excluded.
The weighted predictor again has a material loss on pool 2; ordinary does not.

## Prediction diagnostic

The following averages the four witness columns. It is the expected wrong-action
cost if each predicted probability were used as a decision against its fixed
witness, weighted by own-hand mass. It is not grouped-policy exploitability or
the training cross-entropy objective. Exact-preference costs are zero by definition.

| Split | Seat | Ordinary expected cost | Weighted expected cost |
|---|---:|---:|---:|
| evaluation | 0 | 0.085781218 | 0.085811461 |
| evaluation | 1 | 0.081667653 | 0.037104645 |
| training | 0 | 0.078012485 | 0.076034390 |
| training | 1 | 0.068851786 | 0.034447117 |

Weighting substantially improves this caller diagnostic and its strategic floor.
The bettor diagnostic barely changes on evaluation, while its grouping worsens.
This again illustrates the gap between individual feature diagnostics and the
quality of the induced partition. It does not identify a unique cause.

## Verification and retained execution

Worker: 77.648751 s; worker plus parent: 128.009755 s.
Worker training reconstruction: 8.335468 s; fitting: 0.176358 s.
Combined timing spans launch through parent verification, independent audit and
original result-manifest writing, excluding preflight, reservation and final receipt.
Python 3.14.6 / NumPy 2.5.2 / SciPy 1.18.0, one BLAS thread. Worker limit 600 s,
parent outside it, no RSS cap or peak-memory claim. One invocation completed, exit 0.
All 288 LP calls were counted. Each retained the five-second/10,000-iteration limits.
Four models with 16 output tasks were fitted in the worker and refitted in the
parent for verification. There was no hyperparameter search or launch retry.

The parent reconstructed every training/evaluation input, model, feature and group
and verified all 288 asymmetric payoff certificates with the LP optimizer disabled.
The separate audit used scalar sigmoid/target/cost calculations and independently
assembled regularized gradients. It checked 147,456 probabilities, 16 output
gradients, 144 floor identities, 1,296 signed comparisons, 384 seat contributions
and 2,115 aggregate records, adding no fits or LPs.
Maximum audited gradient: 9.973986e-09.
Maximum new certificate width: 9.287443e-16 chips.
All 477 input pins verified again before retention.
Pre-freeze analytic fits, finite-difference gradients, ties/constants and refusal
checks passed. Certificates apply to encoded binary64 payoffs, not an independent
card evaluator. No cold opposing review is claimed for this diagnostic.

The result is a development intervention on repeatedly observed boards. New-board
confirmation is still required before generalization; full-game or six-max strength
would require separate evaluation. No model was selected per evaluation case.

Original output: D:/Pontius-training/river-abstraction-study/witness-preference-001
Archive: experiments/river-abstraction-study/witness-preference-001
All eleven prior milestones preserved. No production change, commit, push or adoption.

Plan SHA-256:
94e122258da4afbe5774be5fdede69bc90f1a81a8e0db9ebaaf7ed7f9c37f93b

Original result manifest SHA-256:
cc07f034918abf06027b0f5ba2fcec7331ed74bf75bd7388f1eace31b68654b8
