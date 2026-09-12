# Multi-threshold preferences: witness-ordinal-001

## Decisions frozen before scoring

| Decision | Result |
|---|---|
| beats_existing_actual | NOT PASSED |
| beats_existing_floor | NOT PASSED |
| cross_bet_robustness | NOT PASSED |
| ordinal_actual_gain | PASS |
| ordinal_floor_gain | PASS |

Primary: pot-sized mean actual exploitability at 50000 iterations improves
over the previous sign-conditioned predictor by more than 1e-10 chips. The
separate representation flag requires a negative upper endpoint of the mean
certified grouping-floor difference. Practical candidate flags require those
comparisons against both old learned and range-response. Cross-bet robustness
requires both measures to beat all three references in every texture, regime
and omitted-board panel at both bet sizes. No pooled cross-bet acceptance rule.
These descriptive pilot decisions are not confidence levels or adoption.

## Interpretation

At pot size, the actual reduction versus the previous conditioned predictor is
1.16%; at half pot it is
-9.48% (negative means a regression).
The new model is worse than the old learned model on both aggregate panels.
Its small pot-sized gain does not justify replacing the established baseline.
At both bet sizes, even the ordinal grouping's certified lower floor exceeds
the old learned model's actual 50000-iteration score. More iterations within
these fixed groups therefore cannot reverse that aggregate comparison.
The oracle thresholds improve on oracle signs, but remain substantially worse
than clipped continuous advantages. These fixed cutoffs preserve some useful
information without providing a strong learned grouping improvement.

A post-hoc decomposition of the retained certificates attributes most of the
half-pot floor regression against the previous conditioned model to the caller
grouping. This calculation required no additional solves and did not change
any frozen decision rule. It identifies a useful diagnostic target; it does
not establish that threshold crossings caused the loss.

## Full-hand policy exploitability

Lower is better, in conditional river-game chips with pot 10. Every non-oracle
candidate uses the same RegretBR solver and the same iteration checkpoints.
These are enumerated best-response scores within the fixed hand pools, not
sampled match returns, BB/100, or six-max playing-strength measurements.

| Bet | Iterations | Ordinal | Previous conditioned | Old learned | Range-response |
|---|---:|---:|---:|---:|---:|
| 10 | 1000 | 0.0083941295 | 0.0084443640 | 0.0076689298 | 0.0095250960 |
| 10 | 10000 | 0.0067215456 | 0.0067847274 | 0.0058367432 | 0.0079512794 |
| 10 | 50000 | 0.0064778218 | 0.0065539857 | 0.0055737974 | 0.0077211346 |
| 5 | 1000 | 0.0062563043 | 0.0057814425 | 0.0060066912 | 0.0067407187 |
| 5 | 10000 | 0.0047028278 | 0.0043119248 | 0.0045110768 | 0.0051819931 |
| 5 | 50000 | 0.0045264354 | 0.0041346100 | 0.0043265184 | 0.0050122122 |

| Bet | Reference | Actual reduction percent | Floor reduction percent |
|---|---|---:|---:|
| 10 | sign_conditioned | 1.16 | 1.39 |
| 10 | ordinary_preference | -16.22 | -17.04 |
| 10 | range_response | 16.10 | 16.38 |
| 5 | sign_conditioned | -9.48 | -9.61 |
| 5 | ordinary_preference | -4.62 | -4.86 |
| 5 | range_response | 9.69 | 9.86 |

Positive reduction means improvement; negative means worse.

## Representation floors and oracle information

Each floor is the least full-hand profile exploitability representable by that
particular pair of groups. Displayed values are midpoints of retained exact
rational certificate intervals. Oracle-ordinal uses the nine exact threshold
labels, oracle-sign uses only three zero labels, and oracle-clipped uses the
three advantage values clipped to [-0.5,0.5]. Their witness policies are
numerical solutions checked by the same rational certificate procedure.
None is deployable or a bound over all possible groupings. Soft predictions
can distinguish hands tied under hard labels; the hard-label oracle does not
bound the learned model's performance.

| Bet | Grouping | Certified floor | Actual minus floor, 50k |
|---|---|---:|---:|
| 10 | ordinal | 0.0063291148 | 0.0001487069 |
| 10 | sign_conditioned | 0.0064180068 | 0.0001359789 |
| 10 | ordinary_preference | 0.0054075137 | 0.0001662837 |
| 10 | range_response | 0.0075687844 | 0.0001523502 |
| 10 | oracle_ordinal | 0.0138069243 | Not solved iteratively |
| 10 | oracle_sign | 0.0225652620 | Not solved iteratively |
| 10 | oracle_clipped | 0.0021136544 | Not solved iteratively |
| 5 | ordinal | 0.0044341065 | 0.0000923289 |
| 5 | sign_conditioned | 0.0040451655 | 0.0000894445 |
| 5 | ordinary_preference | 0.0042285627 | 0.0000979557 |
| 5 | range_response | 0.0049193448 | 0.0000928674 |
| 5 | oracle_ordinal | 0.0107022253 | Not solved iteratively |
| 5 | oracle_sign | 0.0269020757 | Not solved iteratively |
| 5 | oracle_clipped | 0.0026238437 | Not solved iteratively |

## Board sensitivity and matched differences

Deltas are ordinal minus reference. Counts are lower / higher / numerically
overlapping. Each bet has 32 balanced cases across eight board units.

| Bet | Reference | Actual delta | Case counts | Board counts | Omit-board counts |
|---|---|---:|---:|---:|---:|
| 10 | sign_conditioned | -0.0000761640 | 15/13/4 | 4/3/1 | 7/1/0 |
| 10 | ordinary_preference | 0.0009040244 | 10/20/2 | 2/6/0 | 0/8/0 |
| 10 | range_response | -0.0012433128 | 23/7/2 | 6/2/0 | 8/0/0 |
| 5 | sign_conditioned | 0.0003918254 | 14/17/1 | 3/5/0 | 0/8/0 |
| 5 | ordinary_preference | 0.0001999170 | 12/18/2 | 3/5/0 | 0/8/0 |
| 5 | range_response | -0.0004857768 | 22/8/2 | 7/1/0 | 8/0/0 |

### boards

| Bet | Panel | Reference | Actual delta | Floor lower | Floor upper |
|---|---|---|---:|---:|---:|
| 10 | 0 | sign_conditioned | 0.0000000000 | -0.0000000000 | 0.0000000000 |
| 10 | 0 | ordinary_preference | 0.0052019800 | 0.0053699827 | 0.0053699827 |
| 10 | 0 | range_response | -0.0029625914 | -0.0029632766 | -0.0029632766 |
| 10 | 1 | sign_conditioned | -0.0002365848 | -0.0002364875 | -0.0002364875 |
| 10 | 1 | ordinary_preference | -0.0000283278 | -0.0000344196 | -0.0000344196 |
| 10 | 1 | range_response | -0.0020324686 | -0.0020326757 | -0.0020326757 |
| 10 | 2 | sign_conditioned | 0.0000340719 | 0.0000364744 | 0.0000364744 |
| 10 | 2 | ordinary_preference | 0.0005829816 | 0.0005941694 | 0.0005941694 |
| 10 | 2 | range_response | -0.0009981609 | -0.0009797989 | -0.0009797989 |
| 10 | 3 | sign_conditioned | -0.0005128471 | -0.0005142445 | -0.0005142445 |
| 10 | 3 | ordinary_preference | -0.0011463831 | -0.0011504567 | -0.0011504567 |
| 10 | 3 | range_response | -0.0015775299 | -0.0015701794 | -0.0015701794 |
| 10 | 4 | sign_conditioned | -0.0003346534 | -0.0003361487 | -0.0003361487 |
| 10 | 4 | ordinary_preference | 0.0007110506 | 0.0007307664 | 0.0007307664 |
| 10 | 4 | range_response | 0.0003648058 | 0.0003747709 | 0.0003747709 |
| 10 | 5 | sign_conditioned | 0.0001929746 | 0.0001857324 | 0.0001857324 |
| 10 | 5 | ordinary_preference | 0.0005742914 | 0.0005975541 | 0.0005975541 |
| 10 | 5 | range_response | 0.0010154002 | 0.0010351035 | 0.0010351035 |
| 10 | 6 | sign_conditioned | 0.0012205822 | 0.0011494697 | 0.0011494697 |
| 10 | 6 | ordinary_preference | 0.0004738211 | 0.0004076365 | 0.0004076365 |
| 10 | 6 | range_response | -0.0004149201 | -0.0004172766 | -0.0004172766 |
| 10 | 7 | sign_conditioned | -0.0009728551 | -0.0009959321 | -0.0009959321 |
| 10 | 7 | ordinary_preference | 0.0008627811 | 0.0008575764 | 0.0008575764 |
| 10 | 7 | range_response | -0.0033410381 | -0.0033640243 | -0.0033640243 |
| 5 | 0 | sign_conditioned | 0.0015073619 | 0.0015084463 | 0.0015084463 |
| 5 | 0 | ordinary_preference | -0.0010139743 | -0.0009949096 | -0.0009949096 |
| 5 | 0 | range_response | -0.0006004608 | -0.0005933186 | -0.0005933186 |
| 5 | 1 | sign_conditioned | 0.0007545069 | 0.0007477958 | 0.0007477958 |
| 5 | 1 | ordinary_preference | 0.0009451397 | 0.0009319133 | 0.0009319133 |
| 5 | 1 | range_response | -0.0013124943 | -0.0013162952 | -0.0013162952 |
| 5 | 2 | sign_conditioned | -0.0002817315 | -0.0002877224 | -0.0002877224 |
| 5 | 2 | ordinary_preference | 0.0002875909 | 0.0002935623 | 0.0002935623 |
| 5 | 2 | range_response | -0.0011422085 | -0.0011361892 | -0.0011361892 |
| 5 | 3 | sign_conditioned | -0.0008779208 | -0.0008836703 | -0.0008836703 |
| 5 | 3 | ordinary_preference | -0.0005741451 | -0.0005773840 | -0.0005773840 |
| 5 | 3 | range_response | -0.0002373020 | -0.0002522239 | -0.0002522239 |
| 5 | 4 | sign_conditioned | -0.0003750600 | -0.0003683722 | -0.0003683722 |
| 5 | 4 | ordinary_preference | -0.0000751785 | -0.0000618912 | -0.0000618912 |
| 5 | 4 | range_response | 0.0004315878 | 0.0004483847 | 0.0004483847 |
| 5 | 5 | sign_conditioned | 0.0005650413 | 0.0005642455 | 0.0005642455 |
| 5 | 5 | ordinary_preference | 0.0003154918 | 0.0003223429 | 0.0003223429 |
| 5 | 5 | range_response | -0.0004054275 | -0.0004127892 | -0.0004127892 |
| 5 | 6 | sign_conditioned | 0.0008605013 | 0.0008638896 | 0.0008638896 |
| 5 | 6 | ordinary_preference | 0.0006485188 | 0.0006503774 | 0.0006503774 |
| 5 | 6 | range_response | -0.0000458192 | -0.0000501868 | -0.0000501868 |
| 5 | 7 | sign_conditioned | 0.0009819043 | 0.0009669160 | 0.0009669160 |
| 5 | 7 | ordinary_preference | 0.0010658927 | 0.0010803397 | 0.0010803397 |
| 5 | 7 | range_response | -0.0005740898 | -0.0005692877 | -0.0005692877 |

### textures

| Bet | Panel | Reference | Actual delta | Floor lower | Floor upper |
|---|---|---|---:|---:|---:|
| 10 | multiple-pairs-or-trips | sign_conditioned | 0.0001238635 | 0.0000767688 | 0.0000767688 |
| 10 | multiple-pairs-or-trips | ordinary_preference | 0.0006683011 | 0.0006326064 | 0.0006326064 |
| 10 | multiple-pairs-or-trips | range_response | -0.0018779791 | -0.0018906504 | -0.0018906504 |
| 10 | one-pair | sign_conditioned | -0.0000708394 | -0.0000752081 | -0.0000752081 |
| 10 | one-pair | ordinary_preference | 0.0006426710 | 0.0006641603 | 0.0006641603 |
| 10 | one-pair | range_response | 0.0006901030 | 0.0007049372 | 0.0007049372 |
| 10 | unpaired-flush-possible | sign_conditioned | -0.0002393876 | -0.0002388851 | -0.0002388851 |
| 10 | unpaired-flush-possible | ordinary_preference | -0.0002817008 | -0.0002781437 | -0.0002781437 |
| 10 | unpaired-flush-possible | range_response | -0.0012878454 | -0.0012749892 | -0.0012749892 |
| 10 | unpaired-no-flush | sign_conditioned | -0.0001182924 | -0.0001182438 | -0.0001182438 |
| 10 | unpaired-no-flush | ordinary_preference | 0.0025868261 | 0.0026677816 | 0.0026677816 |
| 10 | unpaired-no-flush | range_response | -0.0024975300 | -0.0024979761 | -0.0024979761 |
| 5 | multiple-pairs-or-trips | sign_conditioned | 0.0009212028 | 0.0009154028 | 0.0009154028 |
| 5 | multiple-pairs-or-trips | ordinary_preference | 0.0008572058 | 0.0008653585 | 0.0008653585 |
| 5 | multiple-pairs-or-trips | range_response | -0.0003099545 | -0.0003097372 | -0.0003097372 |
| 5 | one-pair | sign_conditioned | 0.0000949907 | 0.0000979366 | 0.0000979366 |
| 5 | one-pair | ordinary_preference | 0.0001201567 | 0.0001302259 | 0.0001302259 |
| 5 | one-pair | range_response | 0.0000130801 | 0.0000177977 | 0.0000177977 |
| 5 | unpaired-flush-possible | sign_conditioned | -0.0005798262 | -0.0005856964 | -0.0005856964 |
| 5 | unpaired-flush-possible | ordinary_preference | -0.0001432771 | -0.0001419109 | -0.0001419109 |
| 5 | unpaired-flush-possible | range_response | -0.0006897553 | -0.0006942066 | -0.0006942066 |
| 5 | unpaired-no-flush | sign_conditioned | 0.0011309344 | 0.0011281210 | 0.0011281210 |
| 5 | unpaired-no-flush | ordinary_preference | -0.0000344173 | -0.0000314981 | -0.0000314981 |
| 5 | unpaired-no-flush | range_response | -0.0009564775 | -0.0009548069 | -0.0009548069 |

### regimes

| Bet | Panel | Reference | Actual delta | Floor lower | Floor upper |
|---|---|---|---:|---:|---:|
| 10 | polarized | sign_conditioned | -0.0005222886 | -0.0005446524 | -0.0005446524 |
| 10 | polarized | ordinary_preference | 0.0011835471 | 0.0012159270 | 0.0012159270 |
| 10 | polarized | range_response | -0.0010772272 | -0.0010707689 | -0.0010707689 |
| 10 | uniform | sign_conditioned | 0.0003699606 | 0.0003668683 | 0.0003668683 |
| 10 | uniform | ordinary_preference | 0.0006245017 | 0.0006272753 | 0.0006272753 |
| 10 | uniform | range_response | -0.0014093985 | -0.0014085704 | -0.0014085704 |
| 5 | polarized | sign_conditioned | 0.0003656194 | 0.0003615571 | 0.0003615571 |
| 5 | polarized | ordinary_preference | -0.0001652956 | -0.0001572383 | -0.0001572383 |
| 5 | polarized | range_response | -0.0002239624 | -0.0002233062 | -0.0002233062 |
| 5 | uniform | sign_conditioned | 0.0004180314 | 0.0004163249 | 0.0004163249 |
| 5 | uniform | ordinary_preference | 0.0005651296 | 0.0005683260 | 0.0005683260 |
| 5 | uniform | range_response | -0.0007475911 | -0.0007471703 | -0.0007471703 |

### leave_one_board_out

| Bet | Panel | Reference | Actual delta | Floor lower | Floor upper |
|---|---|---|---:|---:|---:|
| 10 | 0 | sign_conditioned | -0.0000870445 | -0.0001015909 | -0.0001015909 |
| 10 | 0 | ordinary_preference | 0.0002900307 | 0.0002861181 | 0.0002861181 |
| 10 | 0 | range_response | -0.0009977016 | -0.0009934401 | -0.0009934401 |
| 10 | 1 | sign_conditioned | -0.0000532467 | -0.0000678070 | -0.0000678070 |
| 10 | 1 | ordinary_preference | 0.0010372175 | 0.0010581755 | 0.0010581755 |
| 10 | 1 | range_response | -0.0011305763 | -0.0011263830 | -0.0011263830 |
| 10 | 2 | sign_conditioned | -0.0000919119 | -0.0001068015 | -0.0001068015 |
| 10 | 2 | ordinary_preference | 0.0009498876 | 0.0009683771 | 0.0009683771 |
| 10 | 2 | range_response | -0.0012783346 | -0.0012767940 | -0.0012767940 |
| 10 | 3 | sign_conditioned | -0.0000137807 | -0.0000281274 | -0.0000281274 |
| 10 | 3 | ordinary_preference | 0.0011969397 | 0.0012176094 | 0.0012176094 |
| 10 | 3 | range_response | -0.0011955676 | -0.0011924539 | -0.0011924539 |
| 10 | 4 | sign_conditioned | -0.0000392369 | -0.0000535696 | -0.0000535696 |
| 10 | 4 | ordinary_preference | 0.0009315920 | 0.0009488633 | 0.0009488633 |
| 10 | 4 | range_response | -0.0014730441 | -0.0014703040 | -0.0014703040 |
| 10 | 5 | sign_conditioned | -0.0001146123 | -0.0001281241 | -0.0001281241 |
| 10 | 5 | ordinary_preference | 0.0009511291 | 0.0009678936 | 0.0009678936 |
| 10 | 5 | range_response | -0.0015659861 | -0.0015646372 | -0.0015646372 |
| 10 | 6 | sign_conditioned | -0.0002614134 | -0.0002658008 | -0.0002658008 |
| 10 | 6 | ordinary_preference | 0.0009654820 | 0.0009950247 | 0.0009950247 |
| 10 | 6 | range_response | -0.0013616547 | -0.0013571543 | -0.0013571543 |
| 10 | 7 | sign_conditioned | 0.0000519348 | 0.0000406851 | 0.0000406851 |
| 10 | 7 | ordinary_preference | 0.0009099163 | 0.0009307475 | 0.0009307475 |
| 10 | 7 | range_response | -0.0009436378 | -0.0009361904 | -0.0009361904 |
| 5 | 0 | sign_conditioned | 0.0002324631 | 0.0002290117 | 0.0002290117 |
| 5 | 0 | ordinary_preference | 0.0003733300 | 0.0003770372 | 0.0003770372 |
| 5 | 0 | range_response | -0.0004693934 | -0.0004697982 | -0.0004697982 |
| 5 | 1 | sign_conditioned | 0.0003400138 | 0.0003376761 | 0.0003376761 |
| 5 | 1 | ordinary_preference | 0.0000934566 | 0.0001017768 | 0.0001017768 |
| 5 | 1 | range_response | -0.0003676743 | -0.0003665158 | -0.0003665158 |
| 5 | 2 | sign_conditioned | 0.0004880478 | 0.0004856072 | 0.0004856072 |
| 5 | 2 | ordinary_preference | 0.0001873922 | 0.0001929698 | 0.0001929698 |
| 5 | 2 | range_response | -0.0003920008 | -0.0003922452 | -0.0003922452 |
| 5 | 3 | sign_conditioned | 0.0005732177 | 0.0005707427 | 0.0005707427 |
| 5 | 3 | ordinary_preference | 0.0003104973 | 0.0003173907 | 0.0003173907 |
| 5 | 3 | range_response | -0.0005212732 | -0.0005185260 | -0.0005185260 |
| 5 | 4 | sign_conditioned | 0.0005013805 | 0.0004971286 | 0.0004971286 |
| 5 | 4 | ordinary_preference | 0.0002392164 | 0.0002437489 | 0.0002437489 |
| 5 | 4 | range_response | -0.0006168289 | -0.0006186129 | -0.0006186129 |
| 5 | 5 | sign_conditioned | 0.0003670803 | 0.0003638975 | 0.0003638975 |
| 5 | 5 | ordinary_preference | 0.0001834063 | 0.0001888583 | 0.0001888583 |
| 5 | 5 | range_response | -0.0004972553 | -0.0004955881 | -0.0004955881 |
| 5 | 6 | sign_conditioned | 0.0003248717 | 0.0003210912 | 0.0003210912 |
| 5 | 6 | ordinary_preference | 0.0001358310 | 0.0001419962 | 0.0001419962 |
| 5 | 6 | range_response | -0.0005486279 | -0.0005473885 | -0.0005473885 |
| 5 | 7 | sign_conditioned | 0.0003075284 | 0.0003063732 | 0.0003063732 |
| 5 | 7 | ordinary_preference | 0.0000762062 | 0.0000805730 | 0.0000805730 |
| 5 | 7 | range_response | -0.0004731607 | -0.0004732312 | -0.0004732312 |

## Threshold-order diagnostics

Entries are mean own-hand marginal mass with any threshold crossing, averaged
over the three witnesses. Each witness counts once per hand if its later
threshold probability exceeds an earlier one by more than 1e-12. These are
diagnostics only: no sorting or projection changed the feature vectors.

| Bet | Bettor crossing fraction | Caller crossing fraction |
|---|---:|---:|
| 10 | 0.0191268627 | 0.0702945730 |
| 5 | 0.0107479292 | 0.0590016108 |

## Post-hoc seat decomposition

These are additive contributions to the certified floor difference, not new
policy runs: minus half the constrained-bettor value difference plus half the
constrained-caller value difference. Positive means the ordinal grouping is
worse for that contribution. Interval arithmetic is retained in analysis.json;
midpoint sums match the reported floor deltas within 1e-10 chips.

| Bet | Reference | Bettor contribution | Caller contribution |
|---|---|---:|---:|
| 10 | sign_conditioned | 0.0000056923 | -0.0000945843 |
| 10 | ordinary_preference | 0.0003471893 | 0.0005744119 |
| 10 | range_response | -0.0011495272 | -0.0000901425 |
| 5 | sign_conditioned | 0.0000210435 | 0.0003678976 |
| 5 | ordinary_preference | 0.0000300726 | 0.0001754713 |
| 5 | range_response | -0.0004634438 | -0.0000217945 |

## Frozen design and verification

Reuse 64 retained training cells from eight boards, two pools, two regimes and
two bet sizes. Fit nine binary tasks per seat at thresholds -0.25, 0, +0.25
chips, in witness-major order. A computed equality receives label 0.5. The
six zero-threshold fit records exactly reproduce the previous conditioned
model; their predictions match on every evaluated hand. No new training LP.
Inputs and fit settings are unchanged: eleven raw probability features plus
bet/pot, 91 quadratic columns, ordinary ridge-logistic objective with lambda
0.001 on slopes only, and own-hand marginal weights totaling 1/64 per cell.
There was no threshold search or fitting on evaluation data.

Eight new boards were frozen before fitting, two per texture, excluding all
44 previous boards and their suit isomorphisms. Two pools and two regimes at
bets 5 and 10 give 64 evaluation cells. All games have 96 holdings per seat,
pot 10, stacks 20/20, and one heads-up bet with no raises. These are synthetic
conditional ranges and eight board-level units, not 64 independent boards.
The two bet panels are reported separately. This is a fresh-board pilot, not
a population confidence statement.

All nine sigmoid outputs are used directly. Independent heads can cross;
no coherent-distribution claim is made. Group capacities and weighted anchored
clustering stay fixed. Added output heads increase model parameters and
embedding dimension; equal group count is not equal model size or wall time.
The model is written and hashed before any evaluation file exists, then fitting
is disabled. Oracle labels never enter learned prediction. All four non-oracle
policies use unchanged RegretBR at matched 1000/10000/50000 update counts.

Twenty preflight tests passed: six new target/data/audit checks, eight preserved
fit/data checks and six preserved solver checks. The initial label-boundary
test failed as intended against the retained repeated-sign RED scaffold.
No scored-panel rehearsal. All receipts are retained.

The worker made 1024 new LP calls and 18 fits, retaining 256 trajectories and
768 policies. Parent verification disabled LP, rebuilt training cases, checked
384 retained plus 1024 new certificates, reproduced all 18 fits, and then
disabled fitting for evaluation. Every policy was replayed from zero for
12.8 million iterations and checked with independent scalar evaluation.
A separate Fraction audit rebuilt panels, means, certificate differences,
decision flags and crossing frequencies.
Maximum scalar discrepancy: 1.110223e-15 chips.
Independent summary scalar checks: 4,255.
Pinned files checked before and after: 1421.
Worker: 627.372640 s; verifier: 586.142059 s.
Combined invocation: 1213.843737 s, exit 0.
Python 3.14.6, NumPy 2.5.2, SciPy 1.18.0; one BLAS thread; no tracemalloc.
Each subprocess had a 1200-second timeout. No RSS ceiling or peak-memory claim.
All seventeen prior milestones are preserved. No production change, adoption,
commit, push or independent cold review is claimed.

Plan SHA-256:
ea7a42e7559c22e8682b9e76907329fcb5533e7cf54cfa0267321a3baa3da4fc

Candidate SHA-256:
008c65956476440ef13e2405593fad8148d450a487a9551b83557f8cea66e179

Original result manifest SHA-256:
3be77eaf22143435059e0ce3b16f069d130080d0ca60162c2bab498f3c43756f
