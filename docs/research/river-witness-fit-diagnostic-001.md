# Frozen-model fit versus transfer: witness-fit-diagnostic-001

One authorized diagnostic completed 96 observed cases: 48 training and 48 evaluation.
All cases have 96 holdings per seat, three pools and two regimes across eight boards
per split. The saved model, both source milestones and all computational source stayed
unchanged. No refitting, tuning, new boards, grouping score or LP was performed.

## Finding

This is not a uniform transfer failure. Seat 0 has higher evaluation prediction error;
seat 1 has similar error already on training data, with slightly lower evaluation MSE.
Both seats preserve broad correlation with the targets on new boards. That did not
preserve strategic grouping quality in witness-distillation-001.

| Seat | Training MSE | Evaluation MSE | Change |
|---|---:|---:|---:|
| 0: bet minus check | 0.09265071 | 0.15306570 | +65.21% |
| 1: call minus fold, including bet reach | 0.49255715 | 0.46829708 | -4.93% |

MSE is equally averaged across the four witness columns, with equal case weights
and normalized own-hand weights within each case. It is in squared game chips.
Panel composition differs; a raw train/evaluation error ratio is not a causal
estimate of overfitting or an all-board generalization statistic.

| Seat | Split | Correlation across columns | MSE reduction vs training-mean constant |
|---|---|---:|---:|
| 0 | training | 0.9561 to 0.9622 | 91.37% to 92.54% |
| 0 | evaluation | 0.9342 to 0.9408 | 86.76% to 88.15% |
| 1 | training | 0.9138 to 0.9180 | 83.46% to 84.23% |
| 1 | evaluation | 0.9106 to 0.9181 | 82.88% to 84.20% |

The constant baseline is each seat/column's equal-case training target mean,
computed from retained targets; no saved model is fitted again. For training,
this baseline is the weighted training mean. Evaluation retains the same constant.
A large improvement over this weak baseline is not evidence of useful grouping.

## Where action-sign errors occur

A positive predicted advantage chooses bet for seat 0, call for seat 1. Predicted
zero chooses check/fold. Sign rates exclude targets with absolute value <=1e-10
from the conditional denominator. These are per-witness diagnostic responses,
not the actions of the grouped equilibrium policy.

| Seat | Split | Near: abs(target)<=0.1 | Far: abs(target)>0.5 |
|---|---|---:|---:|
| 0 | training | 31.67% to 45.63% | 0.30% to 0.71% |
| 0 | evaluation | 34.78% to 48.59% | 0.42% to 0.64% |
| 1 | training | 43.18% to 46.55% | 0.26% to 0.47% |
| 1 | evaluation | 39.40% to 44.15% | 1.53% to 1.95% |

Ranges span the four witness columns; they are not uncertainty intervals.
The near band has small individual decision costs, so a high error fraction there
does not by itself establish the cause of the prior grouping-floor regression.
Full band masses, MSE, sign rates and cost, including the middle band, are retained.

| Seat | Training mean opportunity cost | Evaluation mean opportunity cost |
|---|---:|---:|
| 0 | 0.01088184 | 0.01583139 |
| 1 | 0.02430938 | 0.03081783 |

Opportunity cost is max(y,0)-y*I(prediction>0), where y is the retained action
advantage against one fixed witness. The table equally averages four separate
witness-response diagnostics; it is not a joint policy value, exploitability,
realized winnings or BB/100. Seat 1 retains the original betting-reach factor.

## Interpretation and next decision

More training boards alone are not established as the remedy. The caller-side
residual and near-boundary errors are present in training as well as evaluation.
The bettor side also shows a transfer gap. Neither observation establishes whether
the limiting factor is features, model capacity, regularization or the objective.
No new model is adopted. The current fixed model remains a retained nonimprovement.

The next useful intervention should test preservation of decision-relevant local
structure, not reward global MSE alone. A bounded follow-up can compare grouping
that retains the existing range/equity features while adding predicted witness
information against the current predicted-only grouping, at the same group budget.
Its strategic floor must be measured; these diagnostics do not guarantee benefit.
This is a recommendation, not authorization for another invocation. These boards
are observed and any tuning on them requires fresh evidence for generalization.

## Verification and provenance

Analytic checks preceded execution: weights, signs, zero predictions, ties, band
boundaries, empty conditional bands and invalid weights. All checks passed.
Fitting and optimizer entry points were replaced with refusal guards during the
diagnostic. Every reconstructed input matched retained inputs, and every evaluation
prediction reproduced the saved prediction exactly. All 157 pinned files matched
before and after execution, including both complete source milestones.

A separate stdlib scalar audit recomputed all 4,928 reported metric values from
the retained hand arrays with no production metric import, new fit, LP or prediction.
Its initial ordering assertion failed because lexical filenames place polarized
before uniform while the plan orders uniform first. The scratch audit was corrected
to follow plan order; the diagnostic was not rerun and no result changed. The incident
is retained in verification-tools/audit-initial-failure.txt.

Worker process time: 17.732143 seconds;
300-second timeout. This spans child execution through exit and excludes parent
preflight and the later scalar audit. Python 3.14.6, NumPy 2.5.2, SciPy 1.18.0,
one BLAS thread. No RSS cap or peak-memory measurement. Exit 0.

This is a post-result diagnostic, not a cold candidate review or a held-out
confirmation. No external reviewer was dispatched for this saved-data analysis.
Existing models, source and previous milestone bytes are preserved. No commit/push.

Original output: D:/Pontius-training/river-abstraction-study/witness-fit-diagnostic-001
Repository archive: experiments/river-abstraction-study/witness-fit-diagnostic-001

Plan SHA-256:
27eb14d933ca71a31e5cb31410800f8296f313c5f53b372c668ff0fd1d320fcd
