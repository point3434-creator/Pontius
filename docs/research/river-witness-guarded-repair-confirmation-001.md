# Guarded repair confirmation 001

Prospective test on 16 new boards, four per texture, excluding all 68 prior
board classes up to suit relabeling. The complete gate was frozen before any
new-board scoring. No fitting, threshold tuning, or repaired-certificate input
to acceptance. One fixed-capacity split/merge per role at 16 groups each.

## Acceptance criteria

| Criterion | Passed |
|---|---|
| exact_nonregression | True |
| useful_half_pot | True |

Every guarded profile must be no worse than original10k by exact comparison.
Utility additionally requires mean half-pot difference below -1e-6 chips.
These are fixed-panel criteria, not population confidence intervals.

## Strategy results

Exploitability in chips; lower is better.

| Bet | Original 10k | Raw repair 10k | Guarded 10k | Original 50k | Reduction % |
|---|---:|---:|---:|---:|---:|
| 10 | 0.029576932 | 0.019598262 | 0.018963221 | 0.029413692 | 35.89 |
| 5 | 0.014322032 | 0.009530822 | 0.009343606 | 0.014208936 | 34.76 |

| Bet | Raw better/equal/worse | Guarded better/equal/worse | Changed accepted |
|---|---|---|---|
| 10 | 30/0/2 | 32/0/0 | 61/64 |
| 5 | 31/0/1 | 32/0/0 | 61/63 |

## boards

| Bet | Panel | Guarded minus original10k |
|---|---|---:|
| 10 | 0 | -0.009228466 |
| 10 | 1 | -0.003854440 |
| 10 | 10 | -0.013644208 |
| 10 | 11 | -0.005416445 |
| 10 | 12 | -0.002303208 |
| 10 | 13 | -0.003313506 |
| 10 | 14 | -0.002726029 |
| 10 | 15 | -0.004543800 |
| 10 | 2 | -0.027976802 |
| 10 | 3 | -0.010056102 |
| 10 | 4 | -0.006546067 |
| 10 | 5 | -0.010396776 |
| 10 | 6 | -0.003082470 |
| 10 | 7 | -0.009954456 |
| 10 | 8 | -0.033740137 |
| 10 | 9 | -0.023036471 |
| 5 | 0 | -0.003336091 |
| 5 | 1 | -0.001442485 |
| 5 | 10 | -0.005116845 |
| 5 | 11 | -0.002885439 |
| 5 | 12 | -0.002150631 |
| 5 | 13 | -0.002184686 |
| 5 | 14 | -0.002436792 |
| 5 | 15 | -0.002133953 |
| 5 | 2 | -0.010269674 |
| 5 | 3 | -0.003181608 |
| 5 | 4 | -0.002902051 |
| 5 | 5 | -0.004519385 |
| 5 | 6 | -0.003528620 |
| 5 | 7 | -0.003622169 |
| 5 | 8 | -0.015777545 |
| 5 | 9 | -0.014166832 |

## textures

| Bet | Panel | Guarded minus original10k |
|---|---|---:|
| 10 | multiple-pairs-or-trips | -0.003221636 |
| 10 | one-pair | -0.018959315 |
| 10 | unpaired-flush-possible | -0.007494942 |
| 10 | unpaired-no-flush | -0.012778953 |
| 5 | multiple-pairs-or-trips | -0.002226515 |
| 5 | one-pair | -0.009486666 |
| 5 | unpaired-flush-possible | -0.003643056 |
| 5 | unpaired-no-flush | -0.004557464 |

## regimes

| Bet | Panel | Guarded minus original10k |
|---|---|---:|
| 10 | polarized | -0.009066640 |
| 10 | uniform | -0.012160783 |
| 5 | polarized | -0.004286254 |
| 5 | uniform | -0.005670597 |

## leave one board out

| Bet | Panel | Guarded minus original10k |
|---|---|---:|
| 10 | 0 | -0.010706061 |
| 10 | 1 | -0.011064330 |
| 10 | 10 | -0.010411678 |
| 10 | 11 | -0.010960196 |
| 10 | 12 | -0.011167745 |
| 10 | 13 | -0.011100392 |
| 10 | 14 | -0.011139557 |
| 10 | 15 | -0.011018372 |
| 10 | 2 | -0.009456172 |
| 10 | 3 | -0.010650885 |
| 10 | 4 | -0.010884888 |
| 10 | 5 | -0.010628174 |
| 10 | 6 | -0.011115794 |
| 10 | 7 | -0.010657662 |
| 10 | 8 | -0.009071950 |
| 10 | 9 | -0.009785528 |
| 5 | 0 | -0.005087914 |
| 5 | 1 | -0.005214155 |
| 5 | 10 | -0.004969197 |
| 5 | 11 | -0.005117958 |
| 5 | 12 | -0.005166945 |
| 5 | 13 | -0.005164675 |
| 5 | 14 | -0.005147868 |
| 5 | 15 | -0.005168057 |
| 5 | 2 | -0.004625675 |
| 5 | 3 | -0.005098213 |
| 5 | 4 | -0.005116850 |
| 5 | 5 | -0.005009028 |
| 5 | 6 | -0.005075079 |
| 5 | 7 | -0.005068842 |
| 5 | 8 | -0.004258484 |
| 5 | 9 | -0.004365865 |

## Measured cost

One pass, one BLAS thread, allocation tracing disabled. Gate time includes
two exact policy evaluations plus validation and selection. It excludes the
independent selected-profile scoring and repaired diagnostic certificate.

Mean gate: 182.559 ms; median 179.289 ms; range 160.313-206.775 ms.
Mean production-path component sum: 1.667 s/case.
Gate share of that component sum: 10.95%.

| Component | Total seconds over 64 cases |
|---|---:|
| preparation | 11.254 |
| baseline_witness | 25.543 |
| proposal | 17.022 |
| acceptance | 11.684 |
| original10k_solver | 20.586 |
| repaired10k_solver | 20.573 |

The component sum includes input preparation, original witness generation,
proposal, original10k and repaired10k setup/updates, and acceptance. It excludes
diagnostic scoring, original40k extra updates, repaired LP, serialization and
verification. It is not an independently timed production invocation.
Original50k compares iterations, not equal wall time or equal total work.

## Verification and scope

64 cases: 16 boards, one pool, two regimes, two bets; 96 holdings per seat.
Pot 10, stacks 20/20, heads-up one-bet river. All compatible deals included.
The model is unchanged, but each game still supplies its own offline witness.
Exact saved-policy safety does not guarantee future retraining, approximate
evaluators, multiway play, full ranges or BB/100 performance.

20 preflight checks and four historical acceptance reproductions passed.
256 asymmetric certificates, 256 saved profiles, and 64 selected profiles checked.
3,840,000 solver updates replayed with verifier LP calls disabled.
128 security pairs reconstructed with independent terminal-payoff sums.
Independent exchange enumerations: 79,485.
Independent aggregate and selection arithmetic checks: 1293.
Worker 242.950 s; verifier 233.138 s; total 476.217 s, exit 0.
Python 3.14.6, NumPy 2.5.2, SciPy 1.18.0; 900 seconds per phase; no hard RSS cap.
All 23 preceding milestone manifests and members verified unchanged.
No production changes, adoption, commit, push or independent cold review.

Plan SHA-256: e0a94349e9ae336391e3d3a45d4c753881edbd2adfab9df3c6bbd77e9c565b30

Results manifest SHA-256: 7ca237cf3f1aae756ed11585414b8aa01a1b76fdab3523e8e4c9b27169404f28
