# Clipped-target learning: witness-clipped-target-001

## Result and decision

Training on clipped targets repairs the two preidentified severe failures, but
does not produce a broadly better grouping method. Mean floor falls by 4.52%
against the previous clipped predictor, while 39 of 48 cases and six of eight
board means worsen. Large improvements in a few cases outweigh smaller regressions
elsewhere. The new mean remains 12.74% worse than range-response grouping and
0.84% worse than range-equity grouping. Do not adopt this candidate as an improvement.

This is a useful mixed result: changing the target can repair the old tail failures,
but target clipping alone does not close the gap to the existing baseline or the
clipped oracle. Prediction error also changes differently by seat. Neither a lower
average prediction error nor one repaired board establishes stronger general play.

## Controlled intervention

One authorized invocation trained two quadratic ridge models on the original 48
training cases. The only target change was clipping each exact witness advantage
to [-0.5,+0.5] game chips before fitting. Eleven inputs, the 78-column basis, four
outputs, lambda=.001, unpenalized intercept, equal-case/own-hand weights, clustering
and occupied group capacity were unchanged. New predictions were clipped before
clustering. Oracle values were targets and diagnostics, not candidate inputs.
All 48 previously observed evaluation cases were retained: eight equally weighted
boards, three hand pools and two range regimes, with 96 holdings per seat.
There was no tuning, new board, control re-solve or omitted case. Exactly 96 new
LP calls evaluated the new groups. The parent separately refit both models for
verification; those two additional fits were not a search.

## Strategic results

Lower is better. Floors are certified numerical intervals for minimum full-hand
exploitability achievable with these groups in the conditional one-bet heads-up
river game. The table gives interval midpoints in game chips, not BB/100 or win rates.

| Method | Mean floor |
|---|---:|
| clipped_oracle | 0.0004702769 |
| clipped_prediction | 0.0060587418 |
| clipped_target_model | 0.0057849204 |
| direct_witness | 0.0022602721 |
| exact | 0.0000000000 |
| predicted_only | 0.0106785993 |
| range_equity | 0.0057369186 |
| range_response | 0.0051313371 |
| uniform_equity_200 | 0.0082456964 |

All deltas are new clipped-target model minus reference. Counts use signed
certificate intervals: lower / higher / overlapping.

| Reference | Mean delta | Counts |
|---|---:|---:|
| clipped_oracle | 0.0053146435 | 0/48/0 |
| clipped_prediction | -0.0002738214 | 9/39/0 |
| direct_witness | 0.0035246484 | 4/44/0 |
| exact | 0.0057849204 | 0/48/0 |
| predicted_only | -0.0048936789 | 44/3/1 |
| range_equity | 0.0000480018 | 26/22/0 |
| range_response | 0.0006535833 | 17/31/0 |
| uniform_equity_200 | -0.0024607760 | 37/11/0 |

## Preidentified failures

Both cases are polarized ranges on board 6h 6s Jh Qc Qd. Both remain included.

| Case | Old clipped | New clipped-target | Range-response | Clipped oracle |
|---|---:|---:|---:|---:|
| b07-p1-polarized | 0.066572339 | 0.004689310 | 0.010144316 | 0.000881500 |
| b07-p2-polarized | 0.048042471 | 0.004408450 | 0.008609137 | 0.000197691 |

## Board and regime sensitivity

| Board | New clipped-target | Old clipped | Range-response |
|---|---:|---:|---:|
| 0 | 0.002519993 | 0.001511494 | 0.003241754 |
| 1 | 0.004185680 | 0.001147098 | 0.003078214 |
| 2 | 0.003181458 | 0.000620810 | 0.001571476 |
| 3 | 0.005696361 | 0.001284344 | 0.003067695 |
| 4 | 0.008318151 | 0.005409107 | 0.008928619 |
| 5 | 0.005809375 | 0.008506653 | 0.003562535 |
| 6 | 0.009495943 | 0.006226558 | 0.008947529 |
| 7 | 0.007072404 | 0.023763871 | 0.008652874 |

Removing board 5 or board 7 reverses the mean advantage against the old
clipped predictor. Every leave-one-board-out comparison against range-response
remains unfavorable. These are sensitivity checks, not confidence intervals;
no board is removed from the main result.

| Reference | Minimum leave-one-board-out delta | Maximum delta |
|---|---:|---:|
| clipped_oracle | 0.0049587419 | 0.0057138792 |
| clipped_prediction | -0.0009432268 | 0.0020715566 |
| direct_witness | 0.0032828736 | 0.0037628149 |
| exact | 0.0052547744 | 0.0062513386 |
| predicted_only | -0.0054260726 | -0.0039435550 |
| range_equity | -0.0001936030 | 0.0002348480 |
| range_response | 0.0003714288 | 0.0009727338 |
| uniform_equity_200 | -0.0027726206 | -0.0016211418 |

| Regime | New clipped-target | Old clipped | Range-response |
|---|---:|---:|---:|
| polarized | 0.005182688 | 0.008937865 | 0.004064202 |
| uniform | 0.006387153 | 0.003179619 | 0.006198472 |

## Prediction diagnostics

Both models are compared after output clipping against the same clipped exact
targets. These values average the four output columns after the retained case
and own-hand weighting. Full per-column values remain in summary.json.

| Split | Seat | Old MSE | New MSE | Old MAE | New MAE |
|---|---|---:|---:|---:|---:|
| evaluation | 0 | 0.02932547 | 0.03458709 | 0.09521526 | 0.13586655 |
| evaluation | 1 | 0.04432066 | 0.03069395 | 0.13200939 | 0.13459052 |
| training | 0 | 0.02354092 | 0.03238017 | 0.08631476 | 0.13356294 |
| training | 1 | 0.04338740 | 0.02524685 | 0.13518338 | 0.12263332 |

Seat 0 MSE worsens on both training and evaluation data; seat 1 MSE improves.
Seat 1 evaluation MAE nevertheless worsens slightly, so its error improvement is
not uniform across metrics. Fitting clipped targets with a regularized quadratic
model does not guarantee better error after nonlinear output clipping. The fixed
regularizer also has a different relative influence at the changed target scale.
This experiment does not isolate those effects. The independently assembled
normal-equation residual checks passed for both fits.

## Verification and execution

Worker: 38.053001 s; worker plus parent: 65.848818 s.
Worker training reconstruction: 8.215151 s; model fitting: 0.015066 s.
The combined boundary spans launch through parent verification and original
results-manifest writing, excluding preflight, output reservation and final receipt.
Python 3.14.6 / NumPy 2.5.2 / SciPy 1.18.0, one BLAS thread. Worker limit 600 s;
parent outside it. No RSS cap or peak-memory claim. Existing five-second and
10,000-iteration per-LP limits remained. Both stages completed with exit 0.

Pre-freeze synthetic checks covered clipping endpoints, interior values, signs,
idempotence, arm separation, invalid inputs and capacity under ties. An analytic
intercept-only example distinguished target clipping from prediction clipping
and checked equal case weight with unequal row counts.
The parent reconstructed training inputs and witness targets, reproduced old
predictions, refit the new models exactly and verified all new groups/certificates
with optimization disabled. The worker counted exactly 96 LP calls.
A separate scalar/rational audit checked 294,912 diagnostic values, 48 floor
identities, 96 asymmetric gaps, 384 signed comparisons and 799 aggregate records.
It added no fits or LP calls. Maximum certificate gap:
6.865281e-16 game chips.
Independently assembled normal-equation maximum residuals:
5.819997e-16, 1.831624e-16.
All 342 input pins verified before retention.
These checks are not a separate implementation of the card evaluator or a cold
opposing review. Numerical certificate widths do not measure board-population
uncertainty. This reused panel supports an intervention result, not a fresh
generalization claim, six-max claim or measured deployed playing-strength gain.

## Retention

All nine previous milestones remain unchanged. Full new models, predictions,
case records, groups, certificates, timings, audit and source diff are retained.
No production source change, commit, push or adoption was performed.

Original output: D:/Pontius-training/river-abstraction-study/witness-clipped-target-001
Repository archive: experiments/river-abstraction-study/witness-clipped-target-001

Plan SHA-256:
5a7bb7fe6e29de0c2f8d1ee15f0375d20446dd6eed32659ba0052eb6d30ff137

Original result manifest SHA-256:
71b669a393c113c7e977a0a16393ebe939556e8c2d3cbecf2050ab34f9f50e5e
