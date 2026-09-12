# Witness-directed group repair 001

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

Exploitability in chips, lower is better. Positive percentage change means
the repair is worse. Floor midpoints are display-only; exact bounds are retained.

| Bet | Original floor | Repaired floor | Original 10k | Repaired 10k | Original 50k |
|---|---:|---:|---:|---:|---:|
| 10 | 0.022154714 | 0.013412908 | 0.022517920 | 0.013802497 | 0.022292723 |
| 5 | 0.011653373 | 0.007431582 | 0.011856035 | 0.007603586 | 0.011721848 |

| Bet | Actual change % | Floor change % | Versus original 50k % |
|---|---:|---:|---:|
| 10 | -38.70 | -39.46 | -38.09 |
| 5 | -35.87 | -36.23 | -35.13 |

## Mechanism and limits

The exchange maximizes improvement against one fixed opponent witness within
the declared one-split/two-other-groups-merge family. The opponent is allowed
to change its response during evaluation, so positive witness gain is not a
guarantee of a lower exploitability floor. No new certificate gates selection.
The original control gets five times as many solver updates, not equal wall
time. Incremental proposal, LP and training times are retained separately.
Prior witness generation and model fitting costs are outside those timings.

| Bet | Changed seats | Floor lower/higher/overlap cases | Board lower/higher/equal |
|---|---:|---|---|
| 10 | 31/32 | 15/0/1 | 8/0/0 |
| 5 | 32/32 | 13/3/0 | 6/2/0 |

## boards

| Bet | Panel | Actual delta | Floor lower | Floor upper |
|---|---|---:|---:|---:|
| 10 | 0 | -0.000442885 | -0.000458652 | -0.000458652 |
| 10 | 1 | -0.027354020 | -0.027376727 | -0.027376727 |
| 10 | 2 | -0.010545568 | -0.010474250 | -0.010474250 |
| 10 | 3 | -0.006052514 | -0.006017234 | -0.006017234 |
| 10 | 4 | -0.010334440 | -0.010349743 | -0.010349743 |
| 10 | 5 | -0.003297969 | -0.003236416 | -0.003236416 |
| 10 | 6 | -0.007029923 | -0.007326289 | -0.007326289 |
| 10 | 7 | -0.004666066 | -0.004695137 | -0.004695137 |
| 5 | 0 | 0.000204460 | 0.000232046 | 0.000232046 |
| 5 | 1 | -0.012908377 | -0.012881665 | -0.012881665 |
| 5 | 2 | -0.010994542 | -0.010911872 | -0.010911872 |
| 5 | 3 | -0.002976933 | -0.002927009 | -0.002927009 |
| 5 | 4 | -0.003713138 | -0.003678957 | -0.003678957 |
| 5 | 5 | -0.002812863 | -0.002812744 | -0.002812744 |
| 5 | 6 | -0.002647135 | -0.002693506 | -0.002693506 |
| 5 | 7 | 0.001828931 | 0.001899381 | 0.001899381 |

## textures

| Bet | Panel | Actual delta | Floor lower | Floor upper |
|---|---|---:|---:|---:|
| 10 | multiple-pairs-or-trips | -0.005847995 | -0.006010713 | -0.006010713 |
| 10 | one-pair | -0.006816204 | -0.006793080 | -0.006793080 |
| 10 | unpaired-flush-possible | -0.008299041 | -0.008245742 | -0.008245742 |
| 10 | unpaired-no-flush | -0.013898452 | -0.013917689 | -0.013917689 |
| 5 | multiple-pairs-or-trips | -0.000409102 | -0.000397063 | -0.000397063 |
| 5 | one-pair | -0.003263000 | -0.003245851 | -0.003245851 |
| 5 | unpaired-flush-possible | -0.006985737 | -0.006919441 | -0.006919441 |
| 5 | unpaired-no-flush | -0.006351958 | -0.006324810 | -0.006324810 |

## regimes

| Bet | Panel | Actual delta | Floor lower | Floor upper |
|---|---|---:|---:|---:|
| 10 | polarized | -0.005783796 | -0.005858002 | -0.005858002 |
| 10 | uniform | -0.011647050 | -0.011625610 | -0.011625610 |
| 5 | polarized | -0.003706963 | -0.003649448 | -0.003649448 |
| 5 | uniform | -0.004797936 | -0.004794134 | -0.004794134 |

## leave one board out

| Bet | Panel | Actual delta | Floor lower | Floor upper |
|---|---|---:|---:|---:|
| 10 | 0 | -0.009897214 | -0.009925114 | -0.009925114 |
| 10 | 1 | -0.006052766 | -0.006079674 | -0.006079674 |
| 10 | 2 | -0.008453974 | -0.008494314 | -0.008494314 |
| 10 | 3 | -0.009095839 | -0.009131031 | -0.009131031 |
| 10 | 4 | -0.008484135 | -0.008512101 | -0.008512101 |
| 10 | 5 | -0.009489345 | -0.009528290 | -0.009528290 |
| 10 | 6 | -0.008956209 | -0.008944023 | -0.008944023 |
| 10 | 7 | -0.009293903 | -0.009319902 | -0.009319902 |
| 5 | 0 | -0.004889151 | -0.004858053 | -0.004858053 |
| 5 | 1 | -0.003015888 | -0.002984666 | -0.002984666 |
| 5 | 2 | -0.003289293 | -0.003266065 | -0.003266065 |
| 5 | 3 | -0.004434666 | -0.004406760 | -0.004406760 |
| 5 | 4 | -0.004329494 | -0.004299339 | -0.004299339 |
| 5 | 5 | -0.004458105 | -0.004423083 | -0.004423083 |
| 5 | 6 | -0.004481780 | -0.004440117 | -0.004440117 |
| 5 | 7 | -0.005121218 | -0.005096244 | -0.005096244 |

## Verification and scope

32 observed cases: eight boards, one pool, two regimes, two bet sizes.
96 holdings per seat, pot 10, stacks 20/20, heads-up one-bet river game.
All compatible deals and unrestricted exact-hand best responses remain.
No population confidence interval or six-max strength claim.

10 author checks passed. 64 new LP calls and 64 trajectories completed.
128 asymmetric certificates and 128 saved profiles verified; 1,920,000
updates replayed with verifier LP calls disabled. The retained 10,000-update
hard policy reproduces exactly in every case.
Independent exchange enumerations: 42,840.
Independent aggregate arithmetic checks: 599.
Worker 91.391 s; verifier 92.173 s; combined 183.618 s, exit 0.
Python 3.14.6, NumPy 2.5.2, SciPy 1.18.0; one BLAS thread; tracing disabled.
900-second limit per phase; no hard RSS cap or memory measurement claim.
All 20 prior milestones verified and preserved. No source changes,
adoption, commit, push or independent cold-review claim.

Plan SHA-256: a59cc604a25b4dd399e7e578aae8f6b35f2dc0751c2f205223a41417c6d65287

Results manifest SHA-256: a264faad832064c72a44e03a5a1acc48aed8ab0b436bbd2550af6844720cbb7e
