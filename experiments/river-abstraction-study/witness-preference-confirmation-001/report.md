# Frozen ordinary-preference confirmation: witness-preference-confirmation-001

## Result and scope

Directional replication: PASS.
Predeclared texture/leave-one-board-out sensitivity: PASS.
The frozen candidate changes mean grouping floor by -23.32% relative to range-response.
Board means: 15 lower, 1 higher, 0 overlapping.
These labels apply to the predeclared numerical mean and sensitivity rules on this
fresh panel. They do not state a statistical confidence level or grant adoption.
The development result replicates directionally on previously unscored boards.
Every selected case is retained; no alternate seed, additional sample or model
adjustment was used. Report the heterogeneous outcomes below with the overall mean.

## Frozen design and new panel

The two ordinary-preference models are copied exactly from witness-preference-001.
No coefficient, input feature, output rule or grouping rule changed. No model was
trained or refitted in this confirmation. The candidate was fixed before selecting
the new boards. All source, producer and plan digests were sealed before scoring.
The fixed classifier was selected using the earlier development results; that
selection is acknowledged, not treated as another independent result.

Sixteen new boards: four in each existing texture category, three fixed hand pools
and two range regimes per board, giving 96 cases. Each game has 96 holdings per
seat, pot 10, bet 5 and stacks 20/20. All 20 earlier study boards are excluded,
including suit-isomorphic equivalents. Hash selection uses the fixed seed
'witness-preference-confirmation-001' and first four accepted boards per texture.
The exact selection attempts and exclusion list are in plan.json. No equity,
prediction, payoff or score was computed during selection. No scoring rehearsal.
Four methods receive two asymmetric solves each: exactly 768 LP calls.
Range-response is the primary baseline, range-equity secondary, exact hands the
numerical reference. Compressed methods match occupied capacity within each case.

The primary endpoint is the equal-board mean candidate-minus-range-response floor.
Its upper numerical endpoint must be negative to pass directional replication.
The separate sensitivity flag requires a negative upper endpoint in every texture
mean and every leave-one-board-out mean. Both rules were frozen before scoring.
There was no post-result effect-size threshold or favorable-subset selection.

## Mean grouping floors

Lower is better. These are certified interval midpoints for the least full-hand
profile exploitability representable by the groups in the encoded one-bet game.
Units are conditional game chips, not win rate or BB/100. Six cases are equally
weighted within each board; all 16 boards and four texture strata have equal weight.

| Method | Mean floor |
|---|---:|
| exact | 0.0000000000 |
| ordinary_preference | 0.0033411789 |
| range_equity | 0.0050084461 |
| range_response | 0.0043571618 |

Delta is candidate minus reference. Counts are lower / higher / overlapping.

| Reference | Mean delta | Counts |
|---|---:|---:|
| exact | 0.0033411789 | 0/95/1 |
| range_equity | -0.0016672672 | 86/9/1 |
| range_response | -0.0010159829 | 70/23/3 |

## Boards and textures

| Board index | Cards (encoded) | Candidate | Range-response | Delta |
|---|---|---:|---:|---:|
| 0 | [2, 13, 17, 26, 47] | 0.002212711 | 0.002593965 | -0.000381254 |
| 1 | [10, 17, 27, 35, 37] | 0.003847771 | 0.004687939 | -0.000840168 |
| 2 | [12, 18, 21, 35, 46] | 0.001795589 | 0.003112993 | -0.001317404 |
| 3 | [1, 7, 18, 33, 36] | 0.001613400 | 0.002384746 | -0.000771346 |
| 4 | [0, 9, 22, 46, 50] | 0.000613891 | 0.001520850 | -0.000906958 |
| 5 | [3, 14, 24, 38, 50] | 0.001178081 | 0.002153959 | -0.000975878 |
| 6 | [3, 6, 31, 41, 47] | 0.000526831 | 0.001233146 | -0.000706315 |
| 7 | [4, 14, 26, 28, 36] | 0.001828960 | 0.002272696 | -0.000443736 |
| 8 | [3, 25, 30, 31, 34] | 0.004002114 | 0.005458301 | -0.001456187 |
| 9 | [6, 9, 13, 36, 37] | 0.001399033 | 0.001882693 | -0.000483660 |
| 10 | [25, 27, 33, 38, 46] | 0.003615720 | 0.005415149 | -0.001799429 |
| 11 | [6, 7, 30, 36, 40] | 0.006326068 | 0.006054570 | 0.000271498 |
| 12 | [1, 12, 13, 36, 38] | 0.007196952 | 0.009898706 | -0.002701753 |
| 13 | [16, 18, 21, 23, 36] | 0.004935679 | 0.006105964 | -0.001170285 |
| 14 | [15, 16, 17, 18, 30] | 0.006188254 | 0.007996625 | -0.001808370 |
| 15 | [6, 14, 15, 20, 23] | 0.006177808 | 0.006942288 | -0.000764480 |

Card encoding is rank index times four plus suit index, as in the frozen code.
The public-card lists are identities, not learned board labels.

| Texture | Candidate | Range-response | Delta | Case counts |
|---|---:|---:|---:|---:|
| multiple-pairs-or-trips | 0.006124673 | 0.007735895 | -0.001611222 | 17/7/0 |
| one-pair | 0.003835734 | 0.004702678 | -0.000866944 | 16/7/1 |
| unpaired-flush-possible | 0.001036941 | 0.001795163 | -0.000758222 | 18/4/2 |
| unpaired-no-flush | 0.002367368 | 0.003194911 | -0.000827543 | 19/5/0 |

| Regime | Candidate | Range-response | Delta | Case counts |
|---|---:|---:|---:|---:|
| polarized | 0.002855458 | 0.003371613 | -0.000516155 | 33/13/2 |
| uniform | 0.003826900 | 0.005342710 | -0.001515810 | 37/10/1 |

The polarized generator keeps the same support and multiplies low/high uniform
showdown-equity hand weights by four for both players, with collision conditioning.
These are synthetic ranges, not posteriors reached through earlier betting.

## Seat contributions

| Reference | Bettor delta | Bettor counts | Caller delta | Caller counts |
|---|---:|---:|---:|---:|
| exact | 0.0010201977 | 0/56/40 | 0.0023209812 | 0/94/2 |
| range_equity | -0.0005926567 | 66/17/13 | -0.0010746104 | 79/15/2 |
| range_response | -0.0003612503 | 55/20/21 | -0.0006547326 | 69/23/4 |

These are the changes in the separate constrained-seat values, with the other
seat unrestricted. They add algebraically to the grouping-floor change, up to
numerical interval handling. They are not results from playing two trained bots.

## Sensitivity and largest losses

| Omitted board | Candidate-minus-response mean |
|---|---:|
| 0 | -0.0010582982 |
| 1 | -0.0010277039 |
| 2 | -0.0009958881 |
| 3 | -0.0010322920 |
| 4 | -0.0010232512 |
| 5 | -0.0010186565 |
| 6 | -0.0010366274 |
| 7 | -0.0010541327 |
| 8 | -0.0009866359 |
| 9 | -0.0010514711 |
| 10 | -0.0009637531 |
| 11 | -0.0011018149 |
| 12 | -0.0009035982 |
| 13 | -0.0010056961 |
| 14 | -0.0009631571 |
| 15 | -0.0010327497 |

All omitted-board panels are descriptive checks; none replaces the full panel.

| Case | Candidate floor | Reference floor | Delta |
|---|---:|---:|---:|
| b15-p2-uniform | 0.016024503 | 0.010639137 | 0.005385365 |
| b12-p0-polarized | 0.008834930 | 0.005162170 | 0.003672760 |
| b14-p0-uniform | 0.008480979 | 0.005319503 | 0.003161476 |
| b00-p1-polarized | 0.005461496 | 0.003034165 | 0.002427332 |
| b14-p0-polarized | 0.010119518 | 0.007949503 | 0.002170015 |

## Execution and verification

Worker: 174.525848 s; worker plus parent: 271.557492 s.
The combined boundary spans launch through parent verification, scalar/rational
audit and result-manifest writing, excluding preflight, reservation and final receipt.
Python 3.14.6 / NumPy 2.5.2 / SciPy 1.18.0, one BLAS thread, no allocation tracing.
Worker limit 600 s, parent outside it, no RSS cap or peak-memory measurement.
One invocation completed with exit 0 and exactly 768 LP calls; zero model fits.

| Worker stage (sum over 96 cases) | Seconds |
|---|---:|
| clustering_seconds | 2.549873 |
| prediction_seconds | 0.005367 |
| preparation_seconds | 16.465734 |
| solve_and_certificate_seconds | 153.561487 |

Prediction timing begins with loaded coefficients and prepared raw features.
Clustering timing begins with predictions and existing capacity. Neither is an
end-to-end live decision benchmark; preparation includes cached board equity work.
The solve stage includes the worker certificate checks. Parent checks are separate.

The parent reconstructed every game, feature and group, verified all 768 asymmetric
certificates with LP calls disabled, and confirmed exact frozen candidate identity.
The independent audit re-derived board selection and suit exclusion, checked 73,728
scalar probabilities, 884,736 collision-conditioned joint cells, 384 floor identities,
288 signed comparisons, 576 seat effects and 1,131 aggregate records. It recomputed
both predeclared result flags and added no LP calls or model fitting.
Maximum certificate width: 2.462101e-15 chips.
All 548 bound files verified again before retention.
All full-hand reference intervals contain the mathematical zero grouping floor.
Synthetic sigmoid, tie capacity, signed interval and suit-invariance checks passed.

Freshness is relative to this study and its pinned exclusion list. Hash-selected,
equally stratified boards are not weighted by real-game reach. Numerical certificates
bound solver error on binary64 payoffs, not population sampling uncertainty. No
formal confidence level, independent card evaluator, cold opposing review, full-pool
coverage, full-game improvement or six-max strength is claimed.

Original output: D:/Pontius-training/river-abstraction-study/witness-preference-confirmation-001
Archive: experiments/river-abstraction-study/witness-preference-confirmation-001
All twelve prior milestones preserved. No production change, commit, push or adoption.

Frozen candidate SHA-256:
ee50b041d7a096fc223082df5b02845a551171bfca062ae8cae22a1e791ad8ce

Plan SHA-256:
6eedadefb5d6f5a3cd516ad6ccc27d5905660d76d517777d207d5c2f24ac36ce

Original result manifest SHA-256:
abba933561e43a69faf723618d0165b166a440543254f60f89a347fdb849cd99
