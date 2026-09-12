# Soft strategy assignment pilot 001

The approved frozen experiment completed and its separate verifier passed.
This compares fixed geometric interpolation against hard assignments using
the same frozen ordinary-preference features and component count. It is an
observed-panel diagnostic, not an Embedding CFR reproduction or a fresh-board
confirmation. No policy was adopted.

## Frozen primary decisions

| Decision | Passed |
|---|---|
| practical_support | False |
| representation_support | False |

Primary: K=16, half-pot. Representation support requires the upper
endpoint of mean soft-minus-hard floor difference below -1e-8 chips. Practical
support also requires 10,000-update mean actual difference below -1e-6 chips.
These are descriptive thresholds, not significance tests.

## All capacity and bet panels

Exploitability is in chips; lower is better. Floor values are certified
interval midpoints for display. Exact rational bounds are retained in JSON.
Positive percentage change means soft is worse; negative means soft is better.

| Bet | K | Hard floor | Soft floor | Hard actual | Soft actual | Actual change % |
|---|---|---:|---:|---:|---:|---:|
| 10 | 16 | 0.022154714 | 0.026354493 | 0.022517920 | 0.026618660 | +18.21 |
| 10 | 32 | 0.007227438 | 0.009626507 | 0.007638551 | 0.010011159 | +31.06 |
| 10 | 8 | 0.041116512 | 0.049731251 | 0.041386512 | 0.049929416 | +20.64 |
| 5 | 16 | 0.011653373 | 0.013123042 | 0.011856035 | 0.013294467 | +12.13 |
| 5 | 32 | 0.004647708 | 0.005882686 | 0.004905809 | 0.006092127 | +24.18 |
| 5 | 8 | 0.017771574 | 0.019366932 | 0.018047053 | 0.019594687 | +8.58 |

## Matched active training time

Three fresh 0.1-second trials per method and cell, each capped at 100,000
updates. Active time excludes assignment building, matrix preparation and
scoring. Actual iteration counts are retained and replayed. These timings
describe this run and do not establish an end-to-end speed advantage.

| Bet | K | Hard actual | Soft actual | Change % |
|---|---|---:|---:|---:|
| 10 | 16 | 0.022858482 | 0.026932443 | +17.82 |
| 10 | 32 | 0.008067464 | 0.010457077 | +29.62 |
| 10 | 8 | 0.041635734 | 0.050117510 | +20.37 |
| 5 | 16 | 0.012094076 | 0.013506075 | +11.68 |
| 5 | 32 | 0.005186438 | 0.006362472 | +22.68 |
| 5 | 8 | 0.018321413 | 0.019859271 | +8.39 |

## boards

| Bet/K | Panel | Actual delta | Floor delta lower | Floor delta upper |
|---|---|---:|---:|---:|
| bet-10-k-16 | 0 | 0.000077987 | 0.000098545 | 0.000098545 |
| bet-10-k-16 | 1 | 0.014447723 | 0.014439917 | 0.014439917 |
| bet-10-k-16 | 2 | 0.003772658 | 0.003806325 | 0.003806325 |
| bet-10-k-16 | 3 | 0.001703104 | 0.001649828 | 0.001649828 |
| bet-10-k-16 | 4 | 0.006831199 | 0.006842771 | 0.006842771 |
| bet-10-k-16 | 5 | 0.003312482 | 0.003746665 | 0.003746665 |
| bet-10-k-16 | 6 | 0.001541008 | 0.001704216 | 0.001704216 |
| bet-10-k-16 | 7 | 0.001119764 | 0.001309957 | 0.001309957 |
| bet-10-k-32 | 0 | 0.000031589 | 0.000041166 | 0.000041166 |
| bet-10-k-32 | 1 | 0.005723523 | 0.005724511 | 0.005724511 |
| bet-10-k-32 | 2 | 0.004928839 | 0.004941908 | 0.004941908 |
| bet-10-k-32 | 3 | 0.001026518 | 0.001000118 | 0.001000118 |
| bet-10-k-32 | 4 | 0.002944147 | 0.002970504 | 0.002970504 |
| bet-10-k-32 | 5 | 0.002261168 | 0.002291516 | 0.002291516 |
| bet-10-k-32 | 6 | 0.001768174 | 0.001767696 | 0.001767696 |
| bet-10-k-32 | 7 | 0.000296910 | 0.000455133 | 0.000455133 |
| bet-10-k-8 | 0 | 0.002166205 | 0.002275132 | 0.002275132 |
| bet-10-k-8 | 1 | 0.008580110 | 0.008579796 | 0.008579796 |
| bet-10-k-8 | 2 | 0.017107653 | 0.017212696 | 0.017212696 |
| bet-10-k-8 | 3 | 0.006814874 | 0.006968352 | 0.006968352 |
| bet-10-k-8 | 4 | 0.005540035 | 0.005587601 | 0.005587601 |
| bet-10-k-8 | 5 | 0.017824991 | 0.017944141 | 0.017944141 |
| bet-10-k-8 | 6 | 0.006679769 | 0.006714001 | 0.006714001 |
| bet-10-k-8 | 7 | 0.003629590 | 0.003636194 | 0.003636194 |
| bet-5-k-16 | 0 | 0.000393506 | 0.000453183 | 0.000453183 |
| bet-5-k-16 | 1 | 0.005423529 | 0.005476483 | 0.005476483 |
| bet-5-k-16 | 2 | 0.000854827 | 0.000941538 | 0.000941538 |
| bet-5-k-16 | 3 | 0.001154134 | 0.001095868 | 0.001095868 |
| bet-5-k-16 | 4 | 0.001004215 | 0.001030742 | 0.001030742 |
| bet-5-k-16 | 5 | 0.000864187 | 0.000850323 | 0.000850323 |
| bet-5-k-16 | 6 | 0.001076316 | 0.001068677 | 0.001068677 |
| bet-5-k-16 | 7 | 0.000736739 | 0.000840539 | 0.000840539 |
| bet-5-k-32 | 0 | 0.000001287 | 0.000005239 | 0.000005239 |
| bet-5-k-32 | 1 | 0.002938053 | 0.002946125 | 0.002946125 |
| bet-5-k-32 | 2 | 0.002226962 | 0.002249554 | 0.002249554 |
| bet-5-k-32 | 3 | 0.000072605 | 0.000010845 | 0.000010845 |
| bet-5-k-32 | 4 | 0.001879646 | 0.001882191 | 0.001882191 |
| bet-5-k-32 | 5 | 0.001143547 | 0.001239147 | 0.001239147 |
| bet-5-k-32 | 6 | 0.001326565 | 0.001363855 | 0.001363855 |
| bet-5-k-32 | 7 | -0.000098123 | 0.000182870 | 0.000182870 |
| bet-5-k-8 | 0 | 0.000431293 | 0.000509088 | 0.000509088 |
| bet-5-k-8 | 1 | 0.006359900 | 0.006385476 | 0.006385476 |
| bet-5-k-8 | 2 | 0.001468619 | 0.001499549 | 0.001499549 |
| bet-5-k-8 | 3 | 0.000306658 | 0.000420475 | 0.000420475 |
| bet-5-k-8 | 4 | -0.001120202 | -0.001082993 | -0.001082993 |
| bet-5-k-8 | 5 | 0.001041303 | 0.001040255 | 0.001040255 |
| bet-5-k-8 | 6 | 0.002154838 | 0.002167367 | 0.002167367 |
| bet-5-k-8 | 7 | 0.001738664 | 0.001823642 | 0.001823642 |

## textures

| Bet/K | Panel | Actual delta | Floor delta lower | Floor delta upper |
|---|---|---:|---:|---:|
| bet-10-k-16 | multiple-pairs-or-trips | 0.001330386 | 0.001507086 | 0.001507086 |
| bet-10-k-16 | one-pair | 0.005071841 | 0.005294718 | 0.005294718 |
| bet-10-k-16 | unpaired-flush-possible | 0.002737881 | 0.002728077 | 0.002728077 |
| bet-10-k-16 | unpaired-no-flush | 0.007262855 | 0.007269231 | 0.007269231 |
| bet-10-k-32 | multiple-pairs-or-trips | 0.001032542 | 0.001111415 | 0.001111415 |
| bet-10-k-32 | one-pair | 0.002602658 | 0.002631010 | 0.002631010 |
| bet-10-k-32 | unpaired-flush-possible | 0.002977679 | 0.002971013 | 0.002971013 |
| bet-10-k-32 | unpaired-no-flush | 0.002877556 | 0.002882839 | 0.002882839 |
| bet-10-k-8 | multiple-pairs-or-trips | 0.005154679 | 0.005175098 | 0.005175098 |
| bet-10-k-8 | one-pair | 0.011682513 | 0.011765871 | 0.011765871 |
| bet-10-k-8 | unpaired-flush-possible | 0.011961264 | 0.012090524 | 0.012090524 |
| bet-10-k-8 | unpaired-no-flush | 0.005373157 | 0.005427464 | 0.005427464 |
| bet-5-k-16 | multiple-pairs-or-trips | 0.000906527 | 0.000954608 | 0.000954608 |
| bet-5-k-16 | one-pair | 0.000934201 | 0.000940533 | 0.000940533 |
| bet-5-k-16 | unpaired-flush-possible | 0.001004481 | 0.001018703 | 0.001018703 |
| bet-5-k-16 | unpaired-no-flush | 0.002908518 | 0.002964833 | 0.002964833 |
| bet-5-k-32 | multiple-pairs-or-trips | 0.000614221 | 0.000773363 | 0.000773363 |
| bet-5-k-32 | one-pair | 0.001511596 | 0.001560669 | 0.001560669 |
| bet-5-k-32 | unpaired-flush-possible | 0.001149783 | 0.001130200 | 0.001130200 |
| bet-5-k-32 | unpaired-no-flush | 0.001469670 | 0.001475682 | 0.001475682 |
| bet-5-k-8 | multiple-pairs-or-trips | 0.001946751 | 0.001995505 | 0.001995505 |
| bet-5-k-8 | one-pair | -0.000039450 | -0.000021369 | -0.000021369 |
| bet-5-k-8 | unpaired-flush-possible | 0.000887638 | 0.000960012 | 0.000960012 |
| bet-5-k-8 | unpaired-no-flush | 0.003395596 | 0.003447282 | 0.003447282 |

## regimes

| Bet/K | Panel | Actual delta | Floor delta lower | Floor delta upper |
|---|---|---:|---:|---:|
| bet-10-k-16 | polarized | 0.003172790 | 0.003347858 | 0.003347858 |
| bet-10-k-16 | uniform | 0.005028691 | 0.005051698 | 0.005051698 |
| bet-10-k-32 | polarized | 0.000949178 | 0.000976923 | 0.000976923 |
| bet-10-k-32 | uniform | 0.003796039 | 0.003821216 | 0.003821216 |
| bet-10-k-8 | polarized | 0.006855325 | 0.006918574 | 0.006918574 |
| bet-10-k-8 | uniform | 0.010230482 | 0.010310904 | 0.010310904 |
| bet-5-k-16 | polarized | 0.001554030 | 0.001601230 | 0.001601230 |
| bet-5-k-16 | uniform | 0.001322833 | 0.001338108 | 0.001338108 |
| bet-5-k-32 | polarized | 0.000662525 | 0.000727272 | 0.000727272 |
| bet-5-k-32 | uniform | 0.001710111 | 0.001742684 | 0.001742684 |
| bet-5-k-8 | polarized | 0.000969789 | 0.001061584 | 0.001061584 |
| bet-5-k-8 | uniform | 0.002125479 | 0.002129131 | 0.002129131 |

## leave one board out

| Bet/K | Panel | Actual delta | Floor delta lower | Floor delta upper |
|---|---|---:|---:|---:|
| bet-10-k-16 | 0 | 0.004675420 | 0.004785669 | 0.004785669 |
| bet-10-k-16 | 1 | 0.002622600 | 0.002736901 | 0.002736901 |
| bet-10-k-16 | 2 | 0.004147610 | 0.004255986 | 0.004255986 |
| bet-10-k-16 | 3 | 0.004443260 | 0.004564057 | 0.004564057 |
| bet-10-k-16 | 4 | 0.003710675 | 0.003822208 | 0.003822208 |
| bet-10-k-16 | 5 | 0.004213349 | 0.004264509 | 0.004264509 |
| bet-10-k-16 | 6 | 0.004466417 | 0.004556287 | 0.004556287 |
| bet-10-k-16 | 7 | 0.004526594 | 0.004612610 | 0.004612610 |
| bet-10-k-32 | 0 | 0.002707040 | 0.002735912 | 0.002735912 |
| bet-10-k-32 | 1 | 0.001893906 | 0.001924006 | 0.001924006 |
| bet-10-k-32 | 2 | 0.002007433 | 0.002035806 | 0.002035806 |
| bet-10-k-32 | 3 | 0.002564907 | 0.002598919 | 0.002598919 |
| bet-10-k-32 | 4 | 0.002290960 | 0.002317436 | 0.002317436 |
| bet-10-k-32 | 5 | 0.002388529 | 0.002414434 | 0.002414434 |
| bet-10-k-32 | 6 | 0.002458956 | 0.002489265 | 0.002489265 |
| bet-10-k-32 | 7 | 0.002669137 | 0.002676774 | 0.002676774 |
| bet-10-k-8 | 0 | 0.009453860 | 0.009520397 | 0.009520397 |
| bet-10-k-8 | 1 | 0.008537588 | 0.008619731 | 0.008619731 |
| bet-10-k-8 | 2 | 0.007319368 | 0.007386460 | 0.007386460 |
| bet-10-k-8 | 3 | 0.008789765 | 0.008849937 | 0.008849937 |
| bet-10-k-8 | 4 | 0.008971885 | 0.009047187 | 0.009047187 |
| bet-10-k-8 | 5 | 0.007216891 | 0.007281967 | 0.007281967 |
| bet-10-k-8 | 6 | 0.008809066 | 0.008886273 | 0.008886273 |
| bet-10-k-8 | 7 | 0.009244805 | 0.009325960 | 0.009325960 |
| bet-5-k-16 | 0 | 0.001587707 | 0.001614882 | 0.001614882 |
| bet-5-k-16 | 1 | 0.000869132 | 0.000897267 | 0.000897267 |
| bet-5-k-16 | 2 | 0.001521804 | 0.001545117 | 0.001545117 |
| bet-5-k-16 | 3 | 0.001479046 | 0.001523070 | 0.001523070 |
| bet-5-k-16 | 4 | 0.001500463 | 0.001532373 | 0.001532373 |
| bet-5-k-16 | 5 | 0.001520467 | 0.001558147 | 0.001558147 |
| bet-5-k-16 | 6 | 0.001490163 | 0.001526954 | 0.001526954 |
| bet-5-k-16 | 7 | 0.001538674 | 0.001559545 | 0.001559545 |
| bet-5-k-32 | 0 | 0.001355608 | 0.001410655 | 0.001410655 |
| bet-5-k-32 | 1 | 0.000936070 | 0.000990529 | 0.000990529 |
| bet-5-k-32 | 2 | 0.001037654 | 0.001090039 | 0.001090039 |
| bet-5-k-32 | 3 | 0.001345419 | 0.001409854 | 0.001409854 |
| bet-5-k-32 | 4 | 0.001087271 | 0.001142519 | 0.001142519 |
| bet-5-k-32 | 5 | 0.001192428 | 0.001234383 | 0.001234383 |
| bet-5-k-32 | 6 | 0.001166282 | 0.001216567 | 0.001216567 |
| bet-5-k-32 | 7 | 0.001369809 | 0.001385279 | 0.001385279 |
| bet-5-k-8 | 0 | 0.001707111 | 0.001750539 | 0.001750539 |
| bet-5-k-8 | 1 | 0.000860168 | 0.000911055 | 0.000911055 |
| bet-5-k-8 | 2 | 0.001558922 | 0.001609044 | 0.001609044 |
| bet-5-k-8 | 3 | 0.001724916 | 0.001763198 | 0.001763198 |
| bet-5-k-8 | 4 | 0.001928753 | 0.001977979 | 0.001977979 |
| bet-5-k-8 | 5 | 0.001619967 | 0.001674658 | 0.001674658 |
| bet-5-k-8 | 6 | 0.001460891 | 0.001513642 | 0.001513642 |
| bet-5-k-8 | 7 | 0.001520344 | 0.001562745 | 0.001562745 |

## Scope and verification

Eight boards, pool 0, two regimes, two bet sizes: 32 games with 96 holdings
per seat, pot 10, stacks 20/20, a single heads-up bet and no raises. Exact
deal enumeration avoids match-sampling noise; it does not supply a board
population confidence interval or six-max playing-strength evidence.

K=8/16/32 crossed with hard/soft gives 192 method-cells. Both seats have K
free action probabilities. Soft adds assignment metadata; this is not an
equal-storage comparison. The fixed interpolation rule is not a learned
embedding and its result must not be generalized to all soft representations.

384 asymmetric LP calls and no fits. The separate verifier reconstructs
original-game rational certificates and all 960 saved profile evaluations.
Every trajectory was replayed: 4,048,110 total updates.
Independent aggregate checks: 1657; all passed.
Fourteen preparation checks passed, including hard-path equality with the
predecessor and independently enumerated soft-policy extrema.
Worker 291.659 s; verifier 248.388 s; combined 540.303 s, exit 0.
Python 3.14.6, NumPy 2.5.2, SciPy 1.18.0; one BLAS thread, no tracing.
Each phase had a 1,800-second timeout. No RSS cap or memory measurement claim.
All 19 preceding milestone manifests and their members verified.
No source changes, adoption, commit, push or independent cold-review claim.

Plan SHA-256: 5fbecc5d02a4fa60e32f621efb052bd01e095b9e33fc1bd888562ab61cddc0e0

Results manifest SHA-256: 0ee546c6f4104287ef5974847881e891e8a7bc35a9dbb5b9ed4032e9f73096b2
