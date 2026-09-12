# Combined-feature intervention: witness-hybrid-001

One authorized invocation completed all 48 already observed evaluation cases.
There were 192 new LP calls and no model refitting, parameter sweep, control
re-solves or case deletion. Eight boards, three pools and two range regimes
are weighted equally within the balanced panel. Each case has 96 holdings per seat.

## Research disposition

Do not adopt the fixed hybrid as an improvement over the strongest existing control.
Restoring the original features reduces the mean floor by 48.25% versus predicted-only
grouping, but hybrid is 3.26% worse than raw11 and 7.70% worse than range_response.
The raw11 control is essential: the repair does not demonstrate incremental value
from these learned predictions. Both raw11 and hybrid improve 45 of 48 cases against
predicted-only. Hybrid is better than raw11 in 21 cases, worse in 25, with two
overlapping numerical intervals. Those overlaps are not assertions of exact equality.

Hybrid improves every board mean against predicted-only. The incremental comparison
against raw11 splits four boards each way; its overall mean is unfavorable, and
removing any one board still leaves hybrid worse on average than raw11.

Hybrid is 3.67% better than range_equity on the overall panel, but only 25 of 48
cases improve, and that small mean benefit changes sign in one leave-one-board-out
check. The stronger range_response control is better on average. There is no basis
to select the weaker comparison as the headline and declare a new best method.

This is an observed-panel intervention, not a fresh held-out confirmation or a
six-max playing-strength result. It tests one fixed training-normalized mixture.
It does not establish that every weighting, predictor or learned abstraction fails.
Future work should address decision-relevant prediction or grouping, rather than
assume another mixture of these same predictions will close the direct-witness gap.

## Mean strategic floors

Lower is better. Values are midpoints of certified intervals in game chips: the
minimum full-hand exploitability achievable with these groups in the conditional
one-bet heads-up river game. They are not a trained-policy win rate or BB/100.
All compressed methods use identical occupied capacity per seat within each case.

| Method | Mean floor |
|---|---:|
| direct_witness | 0.0022602721 |
| exact | 0.0000000000 |
| hybrid | 0.0055264774 |
| predicted_only | 0.0106785993 |
| range_equity | 0.0057369186 |
| range_response | 0.0051313371 |
| raw11 | 0.0053517576 |
| uniform_equity_200 | 0.0082456964 |

## Hybrid comparisons

Negative differences favor hybrid. Counts are lower / higher / overlapping.

| Reference | Mean hybrid-minus-reference | Counts |
|---|---:|---:|
| direct_witness | 0.0032662053 | 2/46/0 |
| exact | 0.0055264774 | 0/48/0 |
| predicted_only | -0.0051521219 | 45/3/0 |
| range_equity | -0.0002104412 | 25/23/0 |
| range_response | 0.0003951403 | 21/25/2 |
| raw11 | 0.0001747198 | 21/25/2 |
| uniform_equity_200 | -0.0027192190 | 35/13/0 |

## Board sensitivity

| Board | Hybrid | Raw11 | Delta predicted-only | Delta raw11 | Delta range-response |
|---|---:|---:|---:|---:|---:|
| 0 | 0.003446868 | 0.003310161 | -0.002900964 | 0.000136707 | 0.000205113 |
| 1 | 0.002890877 | 0.003282410 | -0.005676979 | -0.000391533 | -0.000187337 |
| 2 | 0.001401909 | 0.001461258 | -0.002946472 | -0.000059349 | -0.000169568 |
| 3 | 0.003245591 | 0.003807789 | -0.004975722 | -0.000562198 | 0.000177896 |
| 4 | 0.008809857 | 0.008967622 | -0.001932408 | -0.000157765 | -0.000118762 |
| 5 | 0.004669125 | 0.003417275 | -0.012684795 | 0.001251851 | 0.001106590 |
| 6 | 0.009997683 | 0.009157011 | -0.005007631 | 0.000840672 | 0.001050154 |
| 7 | 0.009749910 | 0.009410534 | -0.005092004 | 0.000339375 | 0.001097036 |

| Leave-one-board-out reference | Minimum mean delta | Maximum mean delta |
|---|---:|---:|
| predicted_only | -0.0056120811 | -0.0040760257 |
| range_equity | -0.0004559694 | 0.0000071634 |
| range_response | 0.0002935046 | 0.0004783513 |
| raw11 | 0.0000208439 | 0.0002799938 |

These are descriptive sensitivity checks, not confidence intervals. The 48 cases
are not 48 independent boards. All board/pool/regime/texture summaries are retained.

## Range regimes

| Regime | Predicted-only | Raw11 | Hybrid | Range-response |
|---|---:|---:|---:|---:|
| polarized | 0.011693584 | 0.004820666 | 0.005083085 | 0.004064202 |
| uniform | 0.009663615 | 0.005882849 | 0.005969870 | 0.006198472 |

## Fixed feature definition

Raw11 contains the nine range-response features plus range and uniform equity.
Hybrid concatenates raw11 and the four saved witness predictions. One scalar per
seat/block is the RMS within-case dispersion over the 48 training cases, using
equal case weights and own-hand marginals. Divide each block by that scalar,
giving equal training within-case distance energy. No per-column standardization,
evaluation-dependent scale or coefficient search. Anchored clustering is unchanged.

| Seat | Raw scale | Prediction scale |
|---|---:|---:|
| 0 | 0.496898714984 | 1.974489577522 |
| 1 | 0.498766616217 | 3.082086652442 |

## Execution and independent verification

Worker: 48.541565 seconds. Worker plus parent: 77.429507 seconds.
The second timer begins before worker launch and ends after parent verification
and results-manifest writing. It excludes preflight, output reservation and writing
the final receipt. Parent work is outside the 600-second worker limit. No RSS cap
or peak-memory measurement. Python 3.14.6 / NumPy 2.5.2 / SciPy 1.18.0; BLAS threads 1.
Existing per-LP five-second and 10,000-iteration limits were preserved. Exit 0.

Pre-execution synthetic checks passed: equal-case weighted scales and offset
invariance, block concatenation, exact occupied capacity even for tied features,
and refusal of invalid/zero scales. Fitting entry points were disabled. The worker
counted exactly 192 LP calls. The parent disabled optimization and reconstructed
every scale/input/feature/group and verified every new certificate and comparison.
All raw inputs and predictions matched their sealed prior records.

The independent scalar/rational audit verified four training-derived scales, 96
new floor identities, 192 asymmetric gap records, 672 signed comparisons and 1,034
aggregate records. It used no extra LP or fit. Maximum new certificate width:
9.902566e-16 chips. This concerns numerical certification
on binary64 payoffs, not board-sampling uncertainty or an independent card evaluator.
All 270 pinned files matched. This is a proportionate standalone research check,
not a claim of a new cold opposing review. No extra reviewer was dispatched.

## Retention

Original output: D:/Pontius-training/river-abstraction-study/witness-hybrid-001
Repository milestone: experiments/river-abstraction-study/witness-hybrid-001
All 48 case results, groups, certificates, comparisons, summaries, scales, source
recipe and audit are retained. All seven earlier milestones remain unchanged.
No production source was modified, and no commit or push was performed.

Plan SHA-256:
1c6427451920593ebb458e724e4a5e82e0df6b3cd17db46cee5d9bacfa056bed

Original result manifest SHA-256:
206a4dd398989b2cc5a994658a2d108bb9e95e19fec1c8d7dd3ea8b347fb5c1e
