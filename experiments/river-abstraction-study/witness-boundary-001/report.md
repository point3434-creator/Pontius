# Boundary-resolution intervention: witness-boundary-001

One authorized invocation completed all 48 observed evaluation cases, with 192 new
LP calls and no model refitting, threshold search, control re-solves or omitted cases.
The fixed transform clips each of four advantage features to [-0.5,+0.5] game chips.
It is applied separately to exact witness values and saved model predictions.

## Main finding and research decision

Boundary-focused grouping is a strong oracle-assisted diagnostic on this panel.
Clipped exact witness features reduce mean floor by 79.19% versus unmodified exact
witness features and 90.84% versus range-response grouping. They improve 43 of 48
cases against the unmodified oracle, with five overlapping intervals and no regression.
They improve all 48 cases against both range controls. Every board mean improves
against the unmodified oracle, and every leave-one-board-out mean remains favorable.
This is the strongest observed oracle-assisted representation in this comparison.
It still uses solved opponent witnesses and is not a cheap deployed improvement.

Clipping predictions helps in 46 cases and reduces their mean floor by 43.26%, but
the other two cases suffer large regressions. The resulting mean is 18.07% worse
than range-response grouping. Do not adopt this learned variant. Its high case-win
count does not compensate for the retained losses in the declared mean endpoint.
The numerical separation between clipped exact and clipped predicted features
identifies a remaining approximation problem under this fixed grouping transform;
it does not by itself diagnose missing information versus model capacity or training loss.

The next targeted learning test is to train the same fixed predictor on clipped
witness targets, rather than learn full-magnitude values and clip only afterward.
That changes the supervised target to match this successful oracle representation.
It should retain architecture, input features and group capacity for a controlled
comparison. Whether it repairs the severe learned regressions remains untested.
This recommendation is not another launch authorization or a claim of success.

## Mean floors

Lower is better. These are midpoints of certified numerical intervals for minimum
full-hand exploitability achievable with the specified groups in the conditional
one-bet heads-up river game. They are not win rates or BB/100. All compressed
methods match occupied capacity within each case. Eight boards have equal weight,
each averaging three hand pools and two range regimes; 96 holdings per seat.

| Method | Mean floor |
|---|---:|
| clipped_oracle | 0.0004702769 |
| clipped_prediction | 0.0060587418 |
| direct_witness | 0.0022602721 |
| exact | 0.0000000000 |
| predicted_only | 0.0106785993 |
| range_equity | 0.0057369186 |
| range_response | 0.0051313371 |
| uniform_equity_200 | 0.0082456964 |

## Paired comparisons

Negative delta favors the new method. Counts are lower / higher / overlapping.

| New method | Reference | Mean delta | Counts |
|---|---|---:|---:|
| clipped_oracle | clipped_prediction | -0.0055884649 | 43/0/5 |
| clipped_oracle | direct_witness | -0.0017899951 | 43/0/5 |
| clipped_oracle | exact | 0.0004702769 | 0/21/27 |
| clipped_oracle | predicted_only | -0.0102083224 | 48/0/0 |
| clipped_oracle | range_equity | -0.0052666417 | 48/0/0 |
| clipped_oracle | range_response | -0.0046610602 | 48/0/0 |
| clipped_oracle | uniform_equity_200 | -0.0077754195 | 48/0/0 |
| clipped_prediction | clipped_oracle | 0.0055884649 | 0/43/5 |
| clipped_prediction | direct_witness | 0.0037984698 | 13/34/1 |
| clipped_prediction | exact | 0.0060587418 | 0/43/5 |
| clipped_prediction | predicted_only | -0.0046198575 | 46/2/0 |
| clipped_prediction | range_equity | 0.0003218232 | 41/7/0 |
| clipped_prediction | range_response | 0.0009274047 | 33/14/1 |
| clipped_prediction | uniform_equity_200 | -0.0021869546 | 45/3/0 |

Twenty-seven clipped-oracle intervals overlap the full-hand control numerically.
This is not a claim of exact mathematical zero exploitability. Neither oracle
clustering rule is globally optimal among partitions, so its improvement is valid
without implying any violation of the full-hand reference.

## Board sensitivity

| Board | Exact witness | Clipped oracle | Predicted-only | Clipped prediction | Range-response |
|---|---:|---:|---:|---:|---:|
| 0 | 0.000662511 | 0.000000000 | 0.006347832 | 0.001511494 | 0.003241754 |
| 1 | 0.000521791 | 0.000003890 | 0.008567855 | 0.001147098 | 0.003078214 |
| 2 | 0.000991528 | 0.000000000 | 0.004348381 | 0.000620810 | 0.001571476 |
| 3 | 0.000479289 | 0.000005521 | 0.008221313 | 0.001284344 | 0.003067695 |
| 4 | 0.004840022 | 0.000895937 | 0.010742264 | 0.005409107 | 0.008928619 |
| 5 | 0.001146873 | 0.000164968 | 0.017353921 | 0.008506653 | 0.003562535 |
| 6 | 0.005023099 | 0.001689988 | 0.015005314 | 0.006226558 | 0.008947529 |
| 7 | 0.004417064 | 0.001001912 | 0.014841914 | 0.023763871 | 0.008652874 |

| Leave-one-board-out contrast | Minimum delta | Maximum delta |
|---|---:|---:|
| clipped_oracle minus direct_witness | -0.0019780276 | -0.0014822680 |
| clipped_oracle minus range_response | -0.0051024293 | -0.0041794000 |
| clipped_prediction minus predicted_only | -0.0065544025 | -0.0040159417 |
| clipped_prediction minus range_response | -0.0010988228 | 0.0015626785 |

These are descriptive sensitivity checks, not confidence intervals. Excluding
board 7 reverses the clipped-prediction mean comparison against range_response.
Board 7 remains included in every main result. No post-hoc exclusion is justified.

## The two regressions against unmodified predictions

| Case | Unmodified floor | Clipped floor | Increase |
|---|---:|---:|---:|
| b07-p1-polarized | 0.005429611 | 0.066572339 | 0.061142728 |
| b07-p2-polarized | 0.029535916 | 0.048042471 | 0.018506555 |

Both use polarized ranges on board 6h 6s Jh Qc Qd, with different hand pools.
This locates the failures; it does not prove their cause or support dropping that
board or range regime. Every comparison against every control is retained.

## Range regimes

| Regime | Clipped oracle | Exact witness | Clipped prediction | Predicted-only | Range-response |
|---|---:|---:|---:|---:|---:|
| polarized | 0.000244889 | 0.001782753 | 0.008937865 | 0.011693584 | 0.004064202 |
| uniform | 0.000695665 | 0.002737791 | 0.003179619 | 0.009663615 | 0.006198472 |

## Interpretation limits

The 0.5-chip threshold was fixed from the preceding diagnostic band before this
run. There was no threshold sweep. These are already observed boards, so even the
large oracle result is an intervention result requiring new reserved evidence
before a generalization claim. It is not a six-max or full-game result.
Clipping preserves signs and inner-band magnitudes while collapsing large same-sign
values. Its allocation of duplicate vectors among occupied anchors is part of the
fixed clustering algorithm. No unique or optimal partition is implied.
Case-win rates and numerical certificate widths do not quantify board-population
uncertainty or replace the declared equal-board mean endpoint.

## Verification and retained execution

Worker: 48.500087 seconds; worker plus parent: 77.715870 seconds.
The latter spans launch through parent verification and results-manifest writing,
excluding preflight, output reservation and final receipt writing. Worker limit:
600 seconds; parent outside it. Python 3.14.6 / NumPy 2.5.2 / SciPy 1.18.0, one
BLAS thread. No RSS cap or peak-memory measurement. Both stages completed, exit 0.
Existing per-LP five-second and 10,000-iteration limits remained unchanged.

Synthetic checks passed for endpoints, interior identity, signs, idempotence, arm
separation, nonfinite/wrong-shape refusal and occupied capacity under ties.
Saved predictions and exact witness advantages were independently reconstructed
from the frozen model and witness policies, respectively. The parent reconstructed
both feature/group paths and verified all new certificates with optimization disabled.
The worker counted exactly 192 LP calls; no model fit occurred.

The separate scalar/rational audit checked all 73,728 clipped values and signs,
96 floor identities, 192 asymmetric gaps, 672 comparisons and 1,034 aggregate
records. It added no fits or LPs. Maximum new certificate width:
6.239366e-16 chips. These certify numerical payoff results,
not a second implementation of the card evaluator. All 161 input pins matched.
An audit-preparation launch initially encountered sandbox access denial; approved
escalation succeeded. The research invocation was not retried and no data changed.
No new cold opposing review was claimed or dispatched for this diagnostic.

Original output: D:/Pontius-training/river-abstraction-study/witness-boundary-001
Repository archive: experiments/river-abstraction-study/witness-boundary-001
All eight earlier milestones and original production source remain unchanged.
No commit, push or deployment. Full groups/features/certificates and reports retained.

Plan SHA-256:
5c9e86c2343c7e01ac226d332c756446577c7ce3785bd40a3c5080b33fddd179

Original result manifest SHA-256:
51966ab55ca840eb56ecc0cc20f46b4ea57539b78d6ec6c8aa0917e7a507e90f
