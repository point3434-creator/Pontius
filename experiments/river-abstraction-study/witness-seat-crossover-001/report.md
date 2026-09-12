# Seat crossover and range-shape diagnostic: witness-seat-crossover-001

## Result and research decision

The two severe failures repaired in the last experiment were predominantly bettor
grouping failures. Swapping only the bettor to the clipped-target model produces
nearly all of both repairs. The caller change improves one slightly and worsens
the other. Across the full panel, the bettor swap reduces mean floor, while the
caller swap raises it. This runs opposite to the preceding squared prediction-error
comparison: bettor MSE worsened and caller MSE improved. Prediction accuracy and
strategic grouping quality must be measured separately.

New bettor plus old caller has the best mean among the four fixed arms: 2.46%
below range-response and 17.39% below old/old. Against range-response it
improves 30 cases, worsens 17 and overlaps one. Seven board means improve, but
five of eight leave-one-board-out comparisons reverse its overall advantage.
Against old/old it improves only three cases, worsens 34 and overlaps 11; seven
board means worsen. Removing board 7 reverses that mean advantage. Keep this as
a diagnostic candidate; do not adopt it as an established improvement.

The synthetic range-shape intervention changes the response to the target change.
Both seat swaps improve the polarized-regime mean and worsen the uniform-regime
mean. However, the bettor improves just two polarized cases and the caller eight.
The average effect must not be read as broad case-by-case success. No causal
claim about natural street progression or polarizing either player alone follows.

## Fixed comparison and estimand

Old = the original quadratic model trained on full targets, with output clipped.
New = the same model recipe trained on clipped targets, with output clipped.
Arm order is bettor (seat 0), caller (seat 1). All four combinations were declared
before execution. Groups, models and witnesses are reused unchanged; each seat
retains the original occupied capacity. No case-specific choice of model is made.
All 48 observed cases remain: eight equal-weight boards x three pools x two regimes,
96 holdings per seat. No new boards, target changes, fits or optimization calls.

With a(G0)=max_XG0 min_Y V and b(G1)=min_YG1 max_X V, the smallest representable
full-hand profile exploitability is E*=[b(G1)-a(G0)]/2. Thus the existing asymmetric
certificates can be crossed. The bettor effect is [a_old-a_new]/2 and the caller
effect [b_new-b_old]/2. They add by construction; this is not a measured discovery
of absent player interaction. The result is specific to the fixed two-player
zero-sum game and its product policy classes. Crossed policies need not form an
equilibrium of the doubly compressed game. The actual model is used to construct
groups; the reported floor benchmarks the best policies those groups can represent.

## Mean grouping floors

Lower is better. Values are certified interval midpoints in conditional game chips.
They are not win rates, BB/100 or full-game/six-max strength measurements.

| Bettor model | Caller model | Mean floor |
|---|---|---:|
| old | old | 0.0060587418 |
| new | old | 0.0050053591 |
| old | new | 0.0068383031 |
| new | new | 0.0057849204 |
| Range-response baseline | Both seats | 0.0051313371 |
| Range-equity baseline | Both seats | 0.0057369186 |
| Clipped exact witness oracle | Both seats | 0.0004702769 |

## Seat effects

Negative favors changing the indicated seat to the new model. Counts are lower /
higher / overlapping, using signed certificate intervals with shared values canceled.

| Regime | Bettor delta | Bettor counts | Caller delta | Caller counts |
|---|---:|---:|---:|---:|
| all | -0.0010533827 | 3/34/11 | 0.0007795613 | 11/37/0 |
| polarized | -0.0032613801 | 2/15/7 | -0.0004937968 | 8/16/0 |
| uniform | 0.0011546147 | 1/19/4 | 0.0020529194 | 3/21/0 |

The 24 matched regime pairs use identical boards and hand pools. The following
contrast is polarized-minus-uniform in the effect of swapping a model. It is not
the raw polarized-minus-uniform floor difference.

| Model swap | Mean difference in effects | Lower / higher / overlapping |
|---|---:|---:|
| bettor | -0.0044159947 | 15/8/1 |
| both | -0.0069627110 | 17/7/0 |
| caller | -0.0025467162 | 18/6/0 |

| Regime | Old/old | New/old | Old/new | New/new | Range-response |
|---|---:|---:|---:|---:|---:|
| polarized | 0.008937865 | 0.005676485 | 0.008444068 | 0.005182688 | 0.004064202 |
| uniform | 0.003179619 | 0.004334233 | 0.005232538 | 0.006387153 | 0.006198472 |

## Preidentified severe cases

| Case | Old/old | New bettor only | New caller only | Both new |
|---|---:|---:|---:|---:|
| b07-p1-polarized | 0.066572339 | 0.004805382 | 0.066456267 | 0.004689310 |
| b07-p2-polarized | 0.048042471 | 0.003976478 | 0.048474443 | 0.004408450 |

Both cases use board 6h 6s Jh Qc Qd and polarized ranges. They stay included.

## Board sensitivity

| Board | Old/old | New/old | Old/new | New/new | Range-response |
|---|---:|---:|---:|---:|---:|
| 0 | 0.001511494 | 0.001974571 | 0.002056917 | 0.002519993 | 0.003241754 |
| 1 | 0.001147098 | 0.001682666 | 0.003650111 | 0.004185680 | 0.003078214 |
| 2 | 0.000620810 | 0.000983850 | 0.002818418 | 0.003181458 | 0.001571476 |
| 3 | 0.001284344 | 0.001998330 | 0.004982374 | 0.005696361 | 0.003067695 |
| 4 | 0.005409107 | 0.006852332 | 0.006874925 | 0.008318151 | 0.008928619 |
| 5 | 0.008506653 | 0.010934680 | 0.003381347 | 0.005809375 | 0.003562535 |
| 6 | 0.006226558 | 0.008946121 | 0.006776379 | 0.009495943 | 0.008947529 |
| 7 | 0.023763871 | 0.006670323 | 0.024165953 | 0.007072404 | 0.008652874 |

| Omitted board | New/old minus old/old | New/old minus range-response |
|---|---:|---:|
| 0 | -0.0012700197 | 0.0000370514 |
| 1 | -0.0012803757 | 0.0000553891 |
| 2 | -0.0012557288 | -0.0000600282 |
| 3 | -0.0013058639 | 0.0000087917 |
| 4 | -0.0014100410 | 0.0001526375 |
| 5 | -0.0015507270 | -0.0011971384 |
| 6 | -0.0015923749 | -0.0001437738 |
| 7 | 0.0012380696 | 0.0001392468 |

These are descriptive sensitivity checks, not confidence intervals. The main
result omits nothing. All arm/reference comparisons and board/pool/texture strata
are in summary.json. None of the four arms constitutes fresh holdout evidence.

## What the range intervention actually changes

For each seat, the retained generator assigns weight four to hands with uniform
showdown equity <=0.2 or >=0.8 and weight one elsewhere. Uniform mode assigns
weight one everywhere. The same hand support is preserved. Joint deals reject
collisions and normalize; card removal therefore changes the effective marginals.
This is a synthetic two-sided reweighting, not a range inferred from prior actions.

| Regime | Seat | Prior low+high mass | Collision-conditioned low+high mass |
|---|---:|---:|---:|
| uniform | 0 | 0.397135 | 0.396845 |
| uniform | 1 | 0.407118 | 0.407245 |
| polarized | 0 | 0.711547 | 0.705253 |
| polarized | 1 | 0.718823 | 0.713007 |

These average the 24 cases per regime. Per-case low/middle/high counts, weights
and masses are retained. Both players change at once, along with the features and
groupings derived from those ranges. The design cannot isolate own-range changes
from opponent-range changes, nor establish that later-street ranges behave this way.

## Verification and retention

Worker: 28.464825 s; worker plus parent: 29.205430 s.
The latter spans worker launch, parent arithmetic audit and result-manifest writing;
it excludes preflight, output reservation and final receipt writing. Python 3.14.6,
NumPy 2.5.2, SciPy 1.18.0, one BLAS thread. Worker limit 600 s, parent outside it.
No RSS cap or peak-memory claim. One invocation completed, exit 0. No retry.

The worker rebuilt all 48 games and matched retained inputs, then freshly verified
192 asymmetric payoff certificates. Fitting and optimization entry points were
disabled; no attempts occurred. The separate audit imported no worker functions
and checked 192 crossed floors, 912 signed case contrasts, 1,222 aggregate records,
24 matched regime pairs and 576 range-mass values against original inputs.
Old/old and new/new exactly reproduce prior floor records. Full crossed group
vectors and constrained policies are saved with their seat provenance.
Maximum inherited certificate width: 6.865281e-16 chips.
Certificates apply to the encoded binary64 payoff matrices. This is not a separate
card-evaluator implementation, cold opposing review, or board-population uncertainty
bound. Synthetic arithmetic/cancellation/feasibility checks passed before freezing.
All 233 bound input files verified again before retention.

Original output: D:/Pontius-training/river-abstraction-study/witness-seat-crossover-001
Archive: experiments/river-abstraction-study/witness-seat-crossover-001
All ten earlier milestones preserved. No production changes, commit, push or adoption.

Plan SHA-256:
2b988ada37d3ec3a016819b50425ec07f2b198b4e13123fc3e0f4309021b02df

Original result manifest SHA-256:
fb32ba5cdf64724453d28317196406ab2061c8fd538566b779d7d385cd58eb95
