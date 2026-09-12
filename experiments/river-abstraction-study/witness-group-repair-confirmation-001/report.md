# Fresh-board witness group repair confirmation 001

Completed under the frozen design. One split and one merge per seat at K=16;
every proposal is scored, including no-ops and regressions. This is offline
refinement using a witness from the evaluation game, not a learned-model
generalization test. No proposal or policy was adopted.

## Frozen primary criteria

| Criterion | Passed |
|---|---|
| practical_support | True |
| representation_support | True |

Half-pot is primary. The mean certified floor-difference upper endpoint
must be below -1e-8 chips; practical support also requires mean actual
10,000-update difference below -1e-6 chips. These are descriptive thresholds.

## All results

Exploitability in chips, lower is better.
Positive percentage change means
the repair is worse. Floor midpoints are display-only; exact bounds are retained.

| Bet | Original floor | Repaired floor | Original 10k | Repaired 10k | Original 50k |
|---|---:|---:|---:|---:|---:|
| 10 | 0.024401376 | 0.015056117 | 0.024700495 | 0.015332533 | 0.024502074 |
| 5 | 0.011861919 | 0.008944266 | 0.012072532 | 0.009133265 | 0.011943736 |

| Bet | Actual change % | Floor change % | Versus original 50k % |
|---|---:|---:|---:|
| 10 | -37.93 | -38.30 | -37.42 |
| 5 | -24.35 | -24.60 | -23.53 |

## Mechanism and limits

The exchange maximizes improvement against one fixed opponent witness within
the declared one-split/two-other-groups-merge family. The opponent is allowed
to change its response during evaluation, so positive witness gain is not a
guarantee of a lower exploitability floor. No new certificate gates selection.
The original control gets five times as many solver updates, not equal wall
time. Incremental proposal, LP and training times are retained separately.
Baseline witness generation is separately timed in every new case. Prior
model fitting is excluded; there is no fitting in this confirmation.

| Bet | Changed seats | Floor lower/higher/overlap cases | Board lower/higher/equal |
|---|---:|---|---|
| 10 | 63/64 | 30/2/0 | 15/1/0 |
| 5 | 64/64 | 28/4/0 | 15/1/0 |

## boards

| Bet | Panel | Actual delta | Floor lower | Floor upper |
|---|---|---:|---:|---:|
| 10 | 0 | -0.022493904 | -0.022428728 | -0.022428728 |
| 10 | 1 | -0.014990387 | -0.014917003 | -0.014917003 |
| 10 | 10 | -0.003408633 | -0.003025745 | -0.003025745 |
| 10 | 11 | -0.014276475 | -0.014359572 | -0.014359572 |
| 10 | 12 | -0.003207777 | -0.003388519 | -0.003388519 |
| 10 | 13 | -0.006548644 | -0.006517239 | -0.006517239 |
| 10 | 14 | -0.003629845 | -0.003708284 | -0.003708284 |
| 10 | 15 | 0.003328186 | 0.003357671 | 0.003357671 |
| 10 | 2 | -0.006793598 | -0.006891654 | -0.006891654 |
| 10 | 3 | -0.021722675 | -0.021728923 | -0.021728923 |
| 10 | 4 | -0.018617214 | -0.018738967 | -0.018738967 |
| 10 | 5 | -0.008699231 | -0.008769854 | -0.008769854 |
| 10 | 6 | -0.005024608 | -0.005016811 | -0.005016811 |
| 10 | 7 | -0.013094566 | -0.013084519 | -0.013084519 |
| 10 | 8 | -0.001769212 | -0.001389757 | -0.001389757 |
| 10 | 9 | -0.008938818 | -0.008916252 | -0.008916252 |
| 5 | 0 | -0.001777838 | -0.001778381 | -0.001778381 |
| 5 | 1 | -0.002691206 | -0.002771444 | -0.002771444 |
| 5 | 10 | -0.000294687 | -0.000013575 | -0.000013575 |
| 5 | 11 | -0.002898655 | -0.002900736 | -0.002900736 |
| 5 | 12 | -0.002418988 | -0.002401022 | -0.002401022 |
| 5 | 13 | -0.002597245 | -0.002509676 | -0.002509676 |
| 5 | 14 | -0.001231774 | -0.001179150 | -0.001179150 |
| 5 | 15 | -0.002945388 | -0.002934393 | -0.002934393 |
| 5 | 2 | -0.001965697 | -0.001926607 | -0.001926607 |
| 5 | 3 | -0.001559958 | -0.001588066 | -0.001588066 |
| 5 | 4 | -0.010806276 | -0.010762076 | -0.010762076 |
| 5 | 5 | -0.003694450 | -0.003757922 | -0.003757922 |
| 5 | 6 | -0.002280201 | -0.002298918 | -0.002298918 |
| 5 | 7 | -0.008422346 | -0.008462374 | -0.008462374 |
| 5 | 8 | 0.000411203 | 0.000414808 | 0.000414808 |
| 5 | 9 | -0.001854769 | -0.001812917 | -0.001812917 |

## textures

| Bet | Panel | Actual delta | Floor lower | Floor upper |
|---|---|---:|---:|---:|
| 10 | multiple-pairs-or-trips | -0.002514520 | -0.002564093 | -0.002564093 |
| 10 | one-pair | -0.007098284 | -0.006922832 | -0.006922832 |
| 10 | unpaired-flush-possible | -0.011358905 | -0.011402538 | -0.011402538 |
| 10 | unpaired-no-flush | -0.016500141 | -0.016491577 | -0.016491577 |
| 5 | multiple-pairs-or-trips | -0.002298349 | -0.002256060 | -0.002256060 |
| 5 | one-pair | -0.001159227 | -0.001078105 | -0.001078105 |
| 5 | unpaired-flush-possible | -0.006300818 | -0.006320322 | -0.006320322 |
| 5 | unpaired-no-flush | -0.001998675 | -0.002016124 | -0.002016124 |

## regimes

| Bet | Panel | Actual delta | Floor lower | Floor upper |
|---|---|---:|---:|---:|
| 10 | polarized | -0.007759524 | -0.007711999 | -0.007711999 |
| 10 | uniform | -0.010976401 | -0.010978521 | -0.010978521 |
| 5 | polarized | -0.003281138 | -0.003262477 | -0.003262477 |
| 5 | uniform | -0.002597396 | -0.002572829 | -0.002572829 |

## leave one board out

| Bet | Panel | Actual delta | Floor lower | Floor upper |
|---|---|---:|---:|---:|
| 10 | 0 | -0.008492900 | -0.008473028 | -0.008473028 |
| 10 | 1 | -0.008993134 | -0.008973810 | -0.008973810 |
| 10 | 10 | -0.009765251 | -0.009766561 | -0.009766561 |
| 10 | 11 | -0.009040729 | -0.009010972 | -0.009010972 |
| 10 | 12 | -0.009778642 | -0.009742376 | -0.009742376 |
| 10 | 13 | -0.009555917 | -0.009533794 | -0.009533794 |
| 10 | 14 | -0.009750504 | -0.009721058 | -0.009721058 |
| 10 | 15 | -0.010214373 | -0.010192122 | -0.010192122 |
| 10 | 2 | -0.009539587 | -0.009508833 | -0.009508833 |
| 10 | 3 | -0.008544315 | -0.008519682 | -0.008519682 |
| 10 | 4 | -0.008751346 | -0.008719013 | -0.008719013 |
| 10 | 5 | -0.009412545 | -0.009383620 | -0.009383620 |
| 10 | 6 | -0.009657520 | -0.009633823 | -0.009633823 |
| 10 | 7 | -0.009119522 | -0.009095976 | -0.009095976 |
| 10 | 8 | -0.009874546 | -0.009875627 | -0.009875627 |
| 10 | 9 | -0.009396572 | -0.009373860 | -0.009373860 |
| 5 | 0 | -0.003016696 | -0.002993604 | -0.002993604 |
| 5 | 1 | -0.002955804 | -0.002927400 | -0.002927400 |
| 5 | 10 | -0.003115572 | -0.003111258 | -0.003111258 |
| 5 | 11 | -0.002941975 | -0.002918781 | -0.002918781 |
| 5 | 12 | -0.002973952 | -0.002952095 | -0.002952095 |
| 5 | 13 | -0.002962069 | -0.002944851 | -0.002944851 |
| 5 | 14 | -0.003053100 | -0.003033553 | -0.003033553 |
| 5 | 15 | -0.002938859 | -0.002916537 | -0.002916537 |
| 5 | 2 | -0.003004172 | -0.002983723 | -0.002983723 |
| 5 | 3 | -0.003031221 | -0.003006292 | -0.003006292 |
| 5 | 4 | -0.002414800 | -0.002394691 | -0.002394691 |
| 5 | 5 | -0.002888922 | -0.002861635 | -0.002861635 |
| 5 | 6 | -0.002983205 | -0.002958902 | -0.002958902 |
| 5 | 7 | -0.002573728 | -0.002548005 | -0.002548005 |
| 5 | 8 | -0.003162632 | -0.003139817 | -0.003139817 |
| 5 | 9 | -0.003011567 | -0.002991302 | -0.002991302 |

## Freshness and worst regressions

All 16 boards were frozen before evaluation. Four per texture, excluding 52
historical board classes up to suit isomorphism. This is the unchanged
one-step algorithm, including a fresh per-game offline witness; it is not a
claim that the learned model alone generalizes to repaired group labels.

| Bet | Worst case | Actual exploitability increase | LOBO means all improve |
|---|---|---:|---|
| 10 | b15-p0-uniform | +0.010603597 | True |
| 5 | b03-p0-uniform | +0.002929200 | True |

## Verification and scope

64 observed cases: sixteen fresh boards, one pool, two regimes, two bet sizes.
96 holdings per seat, pot 10, stacks 20/20, heads-up one-bet river game.
All compatible deals and unrestricted exact-hand best responses remain.
No population confidence interval or six-max strength claim.

16 author checks passed. 256 new LP calls and 128 trajectories completed.
256 asymmetric certificates and 256 saved profiles verified; 3,840,000
updates replayed with verifier LP calls disabled. All new inputs and group
labels were rebuilt. Four historical cases reproduced before the freeze.
A separate stdlib audit compared all 24 suit relabelings with historical boards.
Independent exchange enumerations: 86,310.
Independent aggregate arithmetic checks: 1015.
Worker 210.125 s; verifier 184.374 s; combined 394.596 s, exit 0.
Python 3.14.6, NumPy 2.5.2, SciPy 1.18.0; one BLAS thread; tracing disabled.
900-second limit per phase; no hard RSS cap or memory measurement claim.
All 21 prior milestones verified and preserved. No source changes,
adoption, commit, push or independent cold-review claim.

Plan SHA-256: 941ce0a4d1121cad0d2fdf43076c8871a08b79ef444b3a11547552ee13e42d31

Results manifest SHA-256: 30d51b1d2eca93676c803885f4d0af36580b0abb21812bd1c1967b2a0c869ea1
