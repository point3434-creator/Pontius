# Caller threshold-order diagnostic 001

Completed with the frozen design. This is a no-refit intervention on the
previously observed ordinal-001 panel, not a new-board confirmation.

The intervention projects only caller threshold probabilities into their
required ordering. Bettor groups, trained coefficients, group counts, game
inputs and solver budgets remain fixed. No production strategy was adopted.

The primary mechanism test did not pass. Correcting the probability order
did not deliver the required half-pot score and representation improvements.

## Predeclared decisions

| Diagnostic flag | Passed |
|---|---|
| primary_mechanism_support | False |
| primary_practical_recovery | False |
| secondary_pot_nonregression | True |

Primary mechanism support requires lower half-pot actual exploitability and
a strictly negative certified floor-difference upper bound versus ordinal.
Practical recovery additionally requires those improvements versus both
sign_conditioned and ordinary_preference. Pot non-regression uses 1e-10 chip
tolerance on actual and certified floor upper difference against ordinal.
These are descriptive diagnostic gates, not statistical significance tests.

## Matched 50,000-update results

Values are exploitability in chips; lower is better. Means weight cells
equally within each bet panel. The certified floor is the best representable
profile in these groups; its exact interval is retained in summary.json.

| Bet | Method | Actual exploitability | Floor midpoint |
|---|---|---:|---:|
| 10 | caller_projected | 0.0064778211 | 0.0063291148 |
| 10 | ordinal | 0.0064778218 | 0.0063291148 |
| 10 | sign_conditioned | 0.0065539857 | 0.0064180068 |
| 10 | ordinary_preference | 0.0055737974 | 0.0054075137 |
| 10 | range_response | 0.0077211346 | 0.0075687844 |
| 5 | caller_projected | 0.0045264354 | 0.0044341065 |
| 5 | ordinal | 0.0045264354 | 0.0044341065 |
| 5 | sign_conditioned | 0.0041346100 | 0.0040451655 |
| 5 | ordinary_preference | 0.0043265184 | 0.0042285627 |
| 5 | range_response | 0.0050122122 | 0.0049193448 |

Positive reduction percentages mean improvement; negative means worse.

| Bet | Reference | Actual reduction % | Floor reduction % | Board lower/higher/equal |
|---|---|---:|---:|---|
| 10 | ordinal | 0.000010 | 0.000000 | 1/0/7 |
| 10 | sign_conditioned | 1.162112 | 1.385041 | 4/3/1 |
| 10 | ordinary_preference | -16.219170 | -17.042974 | 2/6/0 |
| 10 | range_response | 16.102731 | 16.378715 | 6/2/0 |
| 5 | ordinal | 0.000000 | -0.000000 | 0/0/8 |
| 5 | sign_conditioned | -9.476720 | -9.614960 | 3/5/0 |
| 5 | ordinary_preference | -4.620736 | -4.860844 | 3/5/0 |
| 5 | range_response | 9.691864 | 9.863880 | 7/1/0 |

## Intervention diagnostics

Crossing mass is averaged across three witnesses under the caller marginal.
Changed-hand mass counts any probability change. Co-membership mass is the
caller-marginal-product mass of pairs whose shared-group status changes.
It is independent of arbitrary group labels. Zero-head shift is the mean
absolute change across the three zero-threshold heads.

| Bet | Crossing before | Crossing after | Changed hands | Zero-head shift | Pair change |
|---|---:|---:|---:|---:|---:|
| 10 | 0.0702945730 | 0.0000000000 | 0.0713480087 | 0.0005271606 | 0.0000478520 |
| 5 | 0.0590016108 | 0.0000000000 | 0.0736739111 | 0.0002270453 | 0.0000000000 |

Bet 10: 31/32 caller partitions unchanged; 1/32 changed, comparing pair membership rather than labels.

Bet 5: 32/32 caller partitions unchanged; 0/32 changed, comparing pair membership rather than labels.

## Sensitivity panels

All predeclared panels follow. Deltas are caller_projected minus reference;
negative is better. Each leave-one-board-out row omits one whole board.
Bounds below are displayed rounded; exact rational endpoints are in JSON.

### checkpoints

| Bet | Panel | Reference | Actual delta | Floor lower | Floor upper |
|---|---|---|---:|---:|---:|
| 10 | 1000 | ordinal | 0.0000000390 | -0.0000000000 | 0.0000000000 |
| 10 | 1000 | sign_conditioned | -0.0000501955 | -0.0000888920 | -0.0000888920 |
| 10 | 1000 | ordinary_preference | 0.0007252388 | 0.0009216012 | 0.0009216012 |
| 10 | 1000 | range_response | -0.0011309275 | -0.0012396696 | -0.0012396696 |
| 10 | 10000 | ordinal | -0.0000000049 | -0.0000000000 | 0.0000000000 |
| 10 | 10000 | sign_conditioned | -0.0000631866 | -0.0000888920 | -0.0000888920 |
| 10 | 10000 | ordinary_preference | 0.0008847975 | 0.0009216012 | 0.0009216012 |
| 10 | 10000 | range_response | -0.0012297387 | -0.0012396696 | -0.0012396696 |
| 10 | 50000 | ordinal | -0.0000000007 | -0.0000000000 | 0.0000000000 |
| 10 | 50000 | sign_conditioned | -0.0000761646 | -0.0000888920 | -0.0000888920 |
| 10 | 50000 | ordinary_preference | 0.0009040237 | 0.0009216012 | 0.0009216012 |
| 10 | 50000 | range_response | -0.0012433135 | -0.0012396696 | -0.0012396696 |
| 5 | 1000 | ordinal | 0.0000000000 | -0.0000000000 | 0.0000000000 |
| 5 | 1000 | sign_conditioned | 0.0004748618 | 0.0003889410 | 0.0003889410 |
| 5 | 1000 | ordinary_preference | 0.0002496131 | 0.0002055439 | 0.0002055439 |
| 5 | 1000 | range_response | -0.0004844145 | -0.0004852382 | -0.0004852382 |
| 5 | 10000 | ordinal | 0.0000000000 | -0.0000000000 | 0.0000000000 |
| 5 | 10000 | sign_conditioned | 0.0003909030 | 0.0003889410 | 0.0003889410 |
| 5 | 10000 | ordinary_preference | 0.0001917509 | 0.0002055439 | 0.0002055439 |
| 5 | 10000 | range_response | -0.0004791653 | -0.0004852382 | -0.0004852382 |
| 5 | 50000 | ordinal | 0.0000000000 | -0.0000000000 | 0.0000000000 |
| 5 | 50000 | sign_conditioned | 0.0003918254 | 0.0003889410 | 0.0003889410 |
| 5 | 50000 | ordinary_preference | 0.0001999170 | 0.0002055439 | 0.0002055439 |
| 5 | 50000 | range_response | -0.0004857768 | -0.0004852382 | -0.0004852382 |

### boards

| Bet | Panel | Reference | Actual delta | Floor lower | Floor upper |
|---|---|---|---:|---:|---:|
| 10 | 0 | ordinal | 0.0000000000 | -0.0000000000 | 0.0000000000 |
| 10 | 0 | sign_conditioned | 0.0000000000 | -0.0000000000 | 0.0000000000 |
| 10 | 0 | ordinary_preference | 0.0052019800 | 0.0053699827 | 0.0053699827 |
| 10 | 0 | range_response | -0.0029625914 | -0.0029632766 | -0.0029632766 |
| 10 | 1 | ordinal | 0.0000000000 | -0.0000000000 | 0.0000000000 |
| 10 | 1 | sign_conditioned | -0.0002365848 | -0.0002364875 | -0.0002364875 |
| 10 | 1 | ordinary_preference | -0.0000283278 | -0.0000344196 | -0.0000344196 |
| 10 | 1 | range_response | -0.0020324686 | -0.0020326757 | -0.0020326757 |
| 10 | 2 | ordinal | 0.0000000000 | -0.0000000000 | 0.0000000000 |
| 10 | 2 | sign_conditioned | 0.0000340719 | 0.0000364744 | 0.0000364744 |
| 10 | 2 | ordinary_preference | 0.0005829816 | 0.0005941694 | 0.0005941694 |
| 10 | 2 | range_response | -0.0009981609 | -0.0009797989 | -0.0009797989 |
| 10 | 3 | ordinal | 0.0000000000 | -0.0000000000 | 0.0000000000 |
| 10 | 3 | sign_conditioned | -0.0005128471 | -0.0005142445 | -0.0005142445 |
| 10 | 3 | ordinary_preference | -0.0011463831 | -0.0011504567 | -0.0011504567 |
| 10 | 3 | range_response | -0.0015775299 | -0.0015701794 | -0.0015701794 |
| 10 | 4 | ordinal | -0.0000000054 | -0.0000000000 | 0.0000000000 |
| 10 | 4 | sign_conditioned | -0.0003346588 | -0.0003361487 | -0.0003361487 |
| 10 | 4 | ordinary_preference | 0.0007110452 | 0.0007307664 | 0.0007307664 |
| 10 | 4 | range_response | 0.0003648004 | 0.0003747709 | 0.0003747709 |
| 10 | 5 | ordinal | 0.0000000000 | -0.0000000000 | 0.0000000000 |
| 10 | 5 | sign_conditioned | 0.0001929746 | 0.0001857324 | 0.0001857324 |
| 10 | 5 | ordinary_preference | 0.0005742914 | 0.0005975541 | 0.0005975541 |
| 10 | 5 | range_response | 0.0010154002 | 0.0010351035 | 0.0010351035 |
| 10 | 6 | ordinal | 0.0000000000 | -0.0000000000 | 0.0000000000 |
| 10 | 6 | sign_conditioned | 0.0012205822 | 0.0011494697 | 0.0011494697 |
| 10 | 6 | ordinary_preference | 0.0004738211 | 0.0004076365 | 0.0004076365 |
| 10 | 6 | range_response | -0.0004149201 | -0.0004172766 | -0.0004172766 |
| 10 | 7 | ordinal | 0.0000000000 | -0.0000000000 | 0.0000000000 |
| 10 | 7 | sign_conditioned | -0.0009728551 | -0.0009959321 | -0.0009959321 |
| 10 | 7 | ordinary_preference | 0.0008627811 | 0.0008575764 | 0.0008575764 |
| 10 | 7 | range_response | -0.0033410381 | -0.0033640243 | -0.0033640243 |
| 5 | 0 | ordinal | 0.0000000000 | -0.0000000000 | 0.0000000000 |
| 5 | 0 | sign_conditioned | 0.0015073619 | 0.0015084463 | 0.0015084463 |
| 5 | 0 | ordinary_preference | -0.0010139743 | -0.0009949096 | -0.0009949096 |
| 5 | 0 | range_response | -0.0006004608 | -0.0005933186 | -0.0005933186 |
| 5 | 1 | ordinal | 0.0000000000 | -0.0000000000 | 0.0000000000 |
| 5 | 1 | sign_conditioned | 0.0007545069 | 0.0007477958 | 0.0007477958 |
| 5 | 1 | ordinary_preference | 0.0009451397 | 0.0009319133 | 0.0009319133 |
| 5 | 1 | range_response | -0.0013124943 | -0.0013162952 | -0.0013162952 |
| 5 | 2 | ordinal | 0.0000000000 | -0.0000000000 | 0.0000000000 |
| 5 | 2 | sign_conditioned | -0.0002817315 | -0.0002877224 | -0.0002877224 |
| 5 | 2 | ordinary_preference | 0.0002875909 | 0.0002935623 | 0.0002935623 |
| 5 | 2 | range_response | -0.0011422085 | -0.0011361892 | -0.0011361892 |
| 5 | 3 | ordinal | 0.0000000000 | -0.0000000000 | 0.0000000000 |
| 5 | 3 | sign_conditioned | -0.0008779208 | -0.0008836703 | -0.0008836703 |
| 5 | 3 | ordinary_preference | -0.0005741451 | -0.0005773840 | -0.0005773840 |
| 5 | 3 | range_response | -0.0002373020 | -0.0002522239 | -0.0002522239 |
| 5 | 4 | ordinal | 0.0000000000 | -0.0000000000 | 0.0000000000 |
| 5 | 4 | sign_conditioned | -0.0003750600 | -0.0003683722 | -0.0003683722 |
| 5 | 4 | ordinary_preference | -0.0000751785 | -0.0000618912 | -0.0000618912 |
| 5 | 4 | range_response | 0.0004315878 | 0.0004483847 | 0.0004483847 |
| 5 | 5 | ordinal | 0.0000000000 | -0.0000000000 | 0.0000000000 |
| 5 | 5 | sign_conditioned | 0.0005650413 | 0.0005642455 | 0.0005642455 |
| 5 | 5 | ordinary_preference | 0.0003154918 | 0.0003223429 | 0.0003223429 |
| 5 | 5 | range_response | -0.0004054275 | -0.0004127892 | -0.0004127892 |
| 5 | 6 | ordinal | 0.0000000000 | -0.0000000000 | 0.0000000000 |
| 5 | 6 | sign_conditioned | 0.0008605013 | 0.0008638896 | 0.0008638896 |
| 5 | 6 | ordinary_preference | 0.0006485188 | 0.0006503774 | 0.0006503774 |
| 5 | 6 | range_response | -0.0000458192 | -0.0000501868 | -0.0000501868 |
| 5 | 7 | ordinal | 0.0000000000 | -0.0000000000 | 0.0000000000 |
| 5 | 7 | sign_conditioned | 0.0009819043 | 0.0009669160 | 0.0009669160 |
| 5 | 7 | ordinary_preference | 0.0010658927 | 0.0010803397 | 0.0010803397 |
| 5 | 7 | range_response | -0.0005740898 | -0.0005692877 | -0.0005692877 |

### textures

| Bet | Panel | Reference | Actual delta | Floor lower | Floor upper |
|---|---|---|---:|---:|---:|
| 10 | multiple-pairs-or-trips | ordinal | 0.0000000000 | -0.0000000000 | 0.0000000000 |
| 10 | multiple-pairs-or-trips | sign_conditioned | 0.0001238635 | 0.0000767688 | 0.0000767688 |
| 10 | multiple-pairs-or-trips | ordinary_preference | 0.0006683011 | 0.0006326064 | 0.0006326064 |
| 10 | multiple-pairs-or-trips | range_response | -0.0018779791 | -0.0018906504 | -0.0018906504 |
| 10 | one-pair | ordinal | -0.0000000027 | -0.0000000000 | 0.0000000000 |
| 10 | one-pair | sign_conditioned | -0.0000708421 | -0.0000752081 | -0.0000752081 |
| 10 | one-pair | ordinary_preference | 0.0006426683 | 0.0006641603 | 0.0006641603 |
| 10 | one-pair | range_response | 0.0006901003 | 0.0007049372 | 0.0007049372 |
| 10 | unpaired-flush-possible | ordinal | 0.0000000000 | -0.0000000000 | 0.0000000000 |
| 10 | unpaired-flush-possible | sign_conditioned | -0.0002393876 | -0.0002388851 | -0.0002388851 |
| 10 | unpaired-flush-possible | ordinary_preference | -0.0002817008 | -0.0002781437 | -0.0002781437 |
| 10 | unpaired-flush-possible | range_response | -0.0012878454 | -0.0012749892 | -0.0012749892 |
| 10 | unpaired-no-flush | ordinal | 0.0000000000 | -0.0000000000 | 0.0000000000 |
| 10 | unpaired-no-flush | sign_conditioned | -0.0001182924 | -0.0001182438 | -0.0001182438 |
| 10 | unpaired-no-flush | ordinary_preference | 0.0025868261 | 0.0026677816 | 0.0026677816 |
| 10 | unpaired-no-flush | range_response | -0.0024975300 | -0.0024979761 | -0.0024979761 |
| 5 | multiple-pairs-or-trips | ordinal | 0.0000000000 | -0.0000000000 | 0.0000000000 |
| 5 | multiple-pairs-or-trips | sign_conditioned | 0.0009212028 | 0.0009154028 | 0.0009154028 |
| 5 | multiple-pairs-or-trips | ordinary_preference | 0.0008572058 | 0.0008653585 | 0.0008653585 |
| 5 | multiple-pairs-or-trips | range_response | -0.0003099545 | -0.0003097372 | -0.0003097372 |
| 5 | one-pair | ordinal | 0.0000000000 | -0.0000000000 | 0.0000000000 |
| 5 | one-pair | sign_conditioned | 0.0000949907 | 0.0000979366 | 0.0000979366 |
| 5 | one-pair | ordinary_preference | 0.0001201567 | 0.0001302259 | 0.0001302259 |
| 5 | one-pair | range_response | 0.0000130801 | 0.0000177977 | 0.0000177977 |
| 5 | unpaired-flush-possible | ordinal | 0.0000000000 | -0.0000000000 | 0.0000000000 |
| 5 | unpaired-flush-possible | sign_conditioned | -0.0005798262 | -0.0005856964 | -0.0005856964 |
| 5 | unpaired-flush-possible | ordinary_preference | -0.0001432771 | -0.0001419109 | -0.0001419109 |
| 5 | unpaired-flush-possible | range_response | -0.0006897553 | -0.0006942066 | -0.0006942066 |
| 5 | unpaired-no-flush | ordinal | 0.0000000000 | -0.0000000000 | 0.0000000000 |
| 5 | unpaired-no-flush | sign_conditioned | 0.0011309344 | 0.0011281210 | 0.0011281210 |
| 5 | unpaired-no-flush | ordinary_preference | -0.0000344173 | -0.0000314981 | -0.0000314981 |
| 5 | unpaired-no-flush | range_response | -0.0009564775 | -0.0009548069 | -0.0009548069 |

### regimes

| Bet | Panel | Reference | Actual delta | Floor lower | Floor upper |
|---|---|---|---:|---:|---:|
| 10 | polarized | ordinal | 0.0000000000 | -0.0000000000 | 0.0000000000 |
| 10 | polarized | sign_conditioned | -0.0005222886 | -0.0005446524 | -0.0005446524 |
| 10 | polarized | ordinary_preference | 0.0011835471 | 0.0012159270 | 0.0012159270 |
| 10 | polarized | range_response | -0.0010772272 | -0.0010707689 | -0.0010707689 |
| 10 | uniform | ordinal | -0.0000000014 | -0.0000000000 | 0.0000000000 |
| 10 | uniform | sign_conditioned | 0.0003699593 | 0.0003668683 | 0.0003668683 |
| 10 | uniform | ordinary_preference | 0.0006245003 | 0.0006272753 | 0.0006272753 |
| 10 | uniform | range_response | -0.0014093999 | -0.0014085704 | -0.0014085704 |
| 5 | polarized | ordinal | 0.0000000000 | -0.0000000000 | 0.0000000000 |
| 5 | polarized | sign_conditioned | 0.0003656194 | 0.0003615571 | 0.0003615571 |
| 5 | polarized | ordinary_preference | -0.0001652956 | -0.0001572383 | -0.0001572383 |
| 5 | polarized | range_response | -0.0002239624 | -0.0002233062 | -0.0002233062 |
| 5 | uniform | ordinal | 0.0000000000 | -0.0000000000 | 0.0000000000 |
| 5 | uniform | sign_conditioned | 0.0004180314 | 0.0004163249 | 0.0004163249 |
| 5 | uniform | ordinary_preference | 0.0005651296 | 0.0005683260 | 0.0005683260 |
| 5 | uniform | range_response | -0.0007475911 | -0.0007471703 | -0.0007471703 |

### leave_one_board_out

| Bet | Panel | Reference | Actual delta | Floor lower | Floor upper |
|---|---|---|---:|---:|---:|
| 10 | 0 | ordinal | -0.0000000008 | -0.0000000000 | 0.0000000000 |
| 10 | 0 | sign_conditioned | -0.0000870453 | -0.0001015909 | -0.0001015909 |
| 10 | 0 | ordinary_preference | 0.0002900299 | 0.0002861181 | 0.0002861181 |
| 10 | 0 | range_response | -0.0009977024 | -0.0009934401 | -0.0009934401 |
| 10 | 1 | ordinal | -0.0000000008 | -0.0000000000 | 0.0000000000 |
| 10 | 1 | sign_conditioned | -0.0000532475 | -0.0000678070 | -0.0000678070 |
| 10 | 1 | ordinary_preference | 0.0010372168 | 0.0010581755 | 0.0010581755 |
| 10 | 1 | range_response | -0.0011305771 | -0.0011263830 | -0.0011263830 |
| 10 | 2 | ordinal | -0.0000000008 | -0.0000000000 | 0.0000000000 |
| 10 | 2 | sign_conditioned | -0.0000919127 | -0.0001068015 | -0.0001068015 |
| 10 | 2 | ordinary_preference | 0.0009498868 | 0.0009683771 | 0.0009683771 |
| 10 | 2 | range_response | -0.0012783353 | -0.0012767940 | -0.0012767940 |
| 10 | 3 | ordinal | -0.0000000008 | -0.0000000000 | 0.0000000000 |
| 10 | 3 | sign_conditioned | -0.0000137814 | -0.0000281274 | -0.0000281274 |
| 10 | 3 | ordinary_preference | 0.0011969389 | 0.0012176094 | 0.0012176094 |
| 10 | 3 | range_response | -0.0011955683 | -0.0011924539 | -0.0011924539 |
| 10 | 4 | ordinal | 0.0000000000 | -0.0000000000 | 0.0000000000 |
| 10 | 4 | sign_conditioned | -0.0000392369 | -0.0000535696 | -0.0000535696 |
| 10 | 4 | ordinary_preference | 0.0009315920 | 0.0009488633 | 0.0009488633 |
| 10 | 4 | range_response | -0.0014730441 | -0.0014703040 | -0.0014703040 |
| 10 | 5 | ordinal | -0.0000000008 | -0.0000000000 | 0.0000000000 |
| 10 | 5 | sign_conditioned | -0.0001146131 | -0.0001281241 | -0.0001281241 |
| 10 | 5 | ordinary_preference | 0.0009511283 | 0.0009678936 | 0.0009678936 |
| 10 | 5 | range_response | -0.0015659869 | -0.0015646372 | -0.0015646372 |
| 10 | 6 | ordinal | -0.0000000008 | -0.0000000000 | 0.0000000000 |
| 10 | 6 | sign_conditioned | -0.0002614142 | -0.0002658008 | -0.0002658008 |
| 10 | 6 | ordinary_preference | 0.0009654812 | 0.0009950247 | 0.0009950247 |
| 10 | 6 | range_response | -0.0013616554 | -0.0013571543 | -0.0013571543 |
| 10 | 7 | ordinal | -0.0000000008 | -0.0000000000 | 0.0000000000 |
| 10 | 7 | sign_conditioned | 0.0000519340 | 0.0000406851 | 0.0000406851 |
| 10 | 7 | ordinary_preference | 0.0009099155 | 0.0009307475 | 0.0009307475 |
| 10 | 7 | range_response | -0.0009436386 | -0.0009361904 | -0.0009361904 |
| 5 | 0 | ordinal | 0.0000000000 | -0.0000000000 | 0.0000000000 |
| 5 | 0 | sign_conditioned | 0.0002324631 | 0.0002290117 | 0.0002290117 |
| 5 | 0 | ordinary_preference | 0.0003733300 | 0.0003770372 | 0.0003770372 |
| 5 | 0 | range_response | -0.0004693934 | -0.0004697982 | -0.0004697982 |
| 5 | 1 | ordinal | 0.0000000000 | -0.0000000000 | 0.0000000000 |
| 5 | 1 | sign_conditioned | 0.0003400138 | 0.0003376761 | 0.0003376761 |
| 5 | 1 | ordinary_preference | 0.0000934566 | 0.0001017768 | 0.0001017768 |
| 5 | 1 | range_response | -0.0003676743 | -0.0003665158 | -0.0003665158 |
| 5 | 2 | ordinal | 0.0000000000 | -0.0000000000 | 0.0000000000 |
| 5 | 2 | sign_conditioned | 0.0004880478 | 0.0004856072 | 0.0004856072 |
| 5 | 2 | ordinary_preference | 0.0001873922 | 0.0001929698 | 0.0001929698 |
| 5 | 2 | range_response | -0.0003920008 | -0.0003922452 | -0.0003922452 |
| 5 | 3 | ordinal | 0.0000000000 | -0.0000000000 | 0.0000000000 |
| 5 | 3 | sign_conditioned | 0.0005732177 | 0.0005707427 | 0.0005707427 |
| 5 | 3 | ordinary_preference | 0.0003104973 | 0.0003173907 | 0.0003173907 |
| 5 | 3 | range_response | -0.0005212732 | -0.0005185260 | -0.0005185260 |
| 5 | 4 | ordinal | 0.0000000000 | -0.0000000000 | 0.0000000000 |
| 5 | 4 | sign_conditioned | 0.0005013805 | 0.0004971286 | 0.0004971286 |
| 5 | 4 | ordinary_preference | 0.0002392164 | 0.0002437489 | 0.0002437489 |
| 5 | 4 | range_response | -0.0006168289 | -0.0006186129 | -0.0006186129 |
| 5 | 5 | ordinal | 0.0000000000 | -0.0000000000 | 0.0000000000 |
| 5 | 5 | sign_conditioned | 0.0003670803 | 0.0003638975 | 0.0003638975 |
| 5 | 5 | ordinary_preference | 0.0001834063 | 0.0001888583 | 0.0001888583 |
| 5 | 5 | range_response | -0.0004972553 | -0.0004955881 | -0.0004955881 |
| 5 | 6 | ordinal | 0.0000000000 | -0.0000000000 | 0.0000000000 |
| 5 | 6 | sign_conditioned | 0.0003248717 | 0.0003210912 | 0.0003210912 |
| 5 | 6 | ordinary_preference | 0.0001358310 | 0.0001419962 | 0.0001419962 |
| 5 | 6 | range_response | -0.0005486279 | -0.0005473885 | -0.0005473885 |
| 5 | 7 | ordinal | 0.0000000000 | -0.0000000000 | 0.0000000000 |
| 5 | 7 | sign_conditioned | 0.0003075284 | 0.0003063732 | 0.0003063732 |
| 5 | 7 | ordinary_preference | 0.0000762062 | 0.0000805730 | 0.0000805730 |
| 5 | 7 | range_response | -0.0004731607 | -0.0004732312 | -0.0004732312 |

## Design and verification

All 64 prior evaluation cells are included: eight boards, two pools, two
regimes, and two bet sizes (5 and 10 chips). Games have 96 holdings per seat,
pot 10, stacks 20/20, a single heads-up bet and no raises. Outcomes and best
responses are enumerated within those games, with no match-sampling noise.
The eight boards are the board-level units. This is not population evidence
or evidence of general-purpose six-max strength.

PAVA uses equal Euclidean weight for the three probabilities within each
witness and no fitted parameters. The original ordinal bettor is unchanged.
Frozen coefficients and raw inputs reproduce prior inference bit for bit.
The projected caller is clustered by the preserved weighted anchored rule;
both occupied group counts are checked. Projection can change the zero head.
No search over thresholds, repair methods or selected favorable cells.

Five preflight tests pass, including exhaustive-partition comparisons on
1,125 triplets. The retained identity scaffold fails four tests as expected.
The scored panel was not rehearsed. The parent independently checked all
18,432 evaluated caller triplets by enumerating equality partitions.

128 new LP calls, zero fits, 64 new trajectories and 192 new checkpoints.
The separate parent verifier forbids LP and fitting, reconstructs the game
inputs and source provenance, checks 640 certificates (128 new, 512 retained),
and replays every new trajectory from zero: 3.2 million iterations. It checks
960 checkpoint scores including all four retained references. Every new
bettor policy is bit-identical to ordinal at every retained checkpoint.
Maximum independent scalar score discrepancy: 1.110223e-15 chips.
Independent rational summary checks: 1,927.
Independent scalar intervention diagnostic checks: 384.
Source and artifact pins checked before and after: 1597.
Worker 130.324160 s; verifier 185.415714 s.
Combined invocation 316.040657 s, exit 0.
Python 3.14.6, NumPy 2.5.2, SciPy 1.18.0; single BLAS thread, no tracemalloc.
Each phase has a 900-second timeout. No RSS cap or measured-memory claim.
All eighteen preceding milestones and pre-existing tracked edits are
preserved; only the research index gains an entry. No source change,
adoption, commit, push or independent cold review.

Plan SHA-256:
b44a481451da99326b19aa7b953cabc5813697f5465f470c45a4743f530027da

Frozen predecessor model SHA-256:
008c65956476440ef13e2405593fad8148d450a487a9551b83557f8cea66e179

Original results manifest SHA-256:
fe605e154e67ddaee1454654178266a2f90030beb1db533422537fdd06bce009
