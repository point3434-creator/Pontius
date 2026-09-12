# Second guarded repair 001

Full-panel follow-up using all 64 accepted first-step states. Sixteen existing
boards, two bets and two regimes; no selection by first-step gain. Second-step
rules were frozen before their outcomes. This is not a fresh-board replication.
Both alternatives use the same per-role security gate against the incumbent.

## Frozen criteria

| Criterion | Passed |
|---|---|
| beats_continuation_half_pot | True |
| exact_nonregression | True |
| useful_second_half_pot | True |

Safety requires both alternatives never worsen the retained first step.
Usefulness requires a half-pot mean gain exceeding 1e-6 chips; the additional
continuation criterion compares the second repair against gated continuation.
These are descriptive fixed-panel criteria, not population confidence intervals.

## Exploitability

Chips, lower is better.
All values use exact-hand best responses.

| Bet | First step | Continue to 20k, gated | Second repair, gated | Original 10k |
|---|---:|---:|---:|---:|
| 10 | 0.018963221 | 0.018868210 | 0.013375485 | 0.029576932 |
| 5 | 0.009343606 | 0.009277929 | 0.006504161 | 0.014322032 |

| Bet | Second-step gain % | Continuation gain % | Gain vs continuation % |
|---|---:|---:|---:|
| 10 | 29.47 | 0.50 | 29.11 |
| 5 | 30.39 | 0.70 | 29.90 |

| Bet | Comparison | Better/equal/worse cases |
|---|---|---|
| 10 | raw_directions | 26/0/6 |
| 10 | second_directions | 30/2/0 |
| 10 | continuation_directions | 32/0/0 |
| 10 | versus_continuation_directions | 30/0/2 |
| 10 | Changed seats accepted | 54/64 |
| 5 | raw_directions | 26/1/5 |
| 5 | second_directions | 31/1/0 |
| 5 | continuation_directions | 32/0/0 |
| 5 | versus_continuation_directions | 30/0/2 |
| 5 | Changed seats accepted | 55/61 |

## boards

| Bet | Panel | Second minus first | Second minus continuation |
|---|---|---:|---:|
| 10 | 0 | -0.005434840 | -0.005360825 |
| 10 | 1 | -0.001558987 | -0.001447535 |
| 10 | 10 | -0.001968378 | -0.001891089 |
| 10 | 11 | -0.001169477 | -0.001063265 |
| 10 | 12 | -0.000764752 | -0.000532310 |
| 10 | 13 | -0.002046704 | -0.001951210 |
| 10 | 14 | -0.001836234 | -0.001740222 |
| 10 | 15 | -0.001912727 | -0.001833526 |
| 10 | 2 | -0.016597708 | -0.016542019 |
| 10 | 3 | -0.009342872 | -0.009227758 |
| 10 | 4 | -0.004781869 | -0.004690349 |
| 10 | 5 | -0.007001674 | -0.006934011 |
| 10 | 6 | -0.002626213 | -0.002543919 |
| 10 | 7 | -0.002384378 | -0.002282623 |
| 10 | 8 | -0.014936886 | -0.014863367 |
| 10 | 9 | -0.015040066 | -0.014979564 |
| 5 | 0 | -0.001058608 | -0.000995338 |
| 5 | 1 | -0.001879979 | -0.001825626 |
| 5 | 10 | -0.002235520 | -0.002169638 |
| 5 | 11 | -0.002081112 | -0.002006885 |
| 5 | 12 | -0.001330370 | -0.001225243 |
| 5 | 13 | -0.000989715 | -0.000928348 |
| 5 | 14 | -0.000874667 | -0.000811994 |
| 5 | 15 | -0.001164910 | -0.001100000 |
| 5 | 2 | -0.007802348 | -0.007761647 |
| 5 | 3 | -0.001406297 | -0.001283871 |
| 5 | 4 | -0.001239597 | -0.001182849 |
| 5 | 5 | -0.001864584 | -0.001815973 |
| 5 | 6 | -0.001588431 | -0.001532628 |
| 5 | 7 | -0.004989731 | -0.004909481 |
| 5 | 8 | -0.007971923 | -0.007923998 |
| 5 | 9 | -0.006953327 | -0.006906770 |

## textures

| Bet | Panel | Second minus first | Second minus continuation |
|---|---|---:|---:|
| 10 | multiple-pairs-or-trips | -0.001640104 | -0.001514317 |
| 10 | one-pair | -0.008278702 | -0.008199321 |
| 10 | unpaired-flush-possible | -0.004198533 | -0.004112726 |
| 10 | unpaired-no-flush | -0.008233602 | -0.008144534 |
| 5 | multiple-pairs-or-trips | -0.001089915 | -0.001016396 |
| 5 | one-pair | -0.004810470 | -0.004751823 |
| 5 | unpaired-flush-possible | -0.002420586 | -0.002360233 |
| 5 | unpaired-no-flush | -0.003036808 | -0.002966621 |

## regimes

| Bet | Panel | Second minus first | Second minus continuation |
|---|---|---:|---:|
| 10 | polarized | -0.004729236 | -0.004623516 |
| 10 | uniform | -0.006446234 | -0.006361933 |
| 5 | polarized | -0.002682042 | -0.002607223 |
| 5 | uniform | -0.002996848 | -0.002940313 |

## leave one board out

| Bet | Panel | Second minus first | Second minus continuation |
|---|---|---:|---:|
| 10 | 0 | -0.005597928 | -0.005501518 |
| 10 | 1 | -0.005856319 | -0.005762404 |
| 10 | 10 | -0.005829026 | -0.005732834 |
| 10 | 11 | -0.005882286 | -0.005788022 |
| 10 | 12 | -0.005909267 | -0.005823419 |
| 10 | 13 | -0.005823804 | -0.005728826 |
| 10 | 14 | -0.005837835 | -0.005742891 |
| 10 | 15 | -0.005832736 | -0.005736671 |
| 10 | 2 | -0.004853737 | -0.004756105 |
| 10 | 3 | -0.005337393 | -0.005243722 |
| 10 | 4 | -0.005641460 | -0.005546216 |
| 10 | 5 | -0.005493473 | -0.005396639 |
| 10 | 6 | -0.005785170 | -0.005689312 |
| 10 | 7 | -0.005801292 | -0.005706731 |
| 10 | 8 | -0.004964459 | -0.004868015 |
| 10 | 9 | -0.004957580 | -0.004860269 |
| 5 | 0 | -0.002958167 | -0.002892330 |
| 5 | 1 | -0.002903409 | -0.002836978 |
| 5 | 10 | -0.002879707 | -0.002814043 |
| 5 | 11 | -0.002890000 | -0.002824894 |
| 5 | 12 | -0.002940050 | -0.002877003 |
| 5 | 13 | -0.002962760 | -0.002896796 |
| 5 | 14 | -0.002970430 | -0.002904553 |
| 5 | 15 | -0.002951081 | -0.002885353 |
| 5 | 2 | -0.002508585 | -0.002441243 |
| 5 | 3 | -0.002934988 | -0.002873095 |
| 5 | 4 | -0.002946101 | -0.002879829 |
| 5 | 5 | -0.002904436 | -0.002837621 |
| 5 | 6 | -0.002922846 | -0.002856511 |
| 5 | 7 | -0.002696093 | -0.002631387 |
| 5 | 8 | -0.002497280 | -0.002430419 |
| 5 | 9 | -0.002565186 | -0.002498235 |

## Incremental computation

| Bet | Second step seconds/case | Continuation seconds/case | Cost ratio |
|---|---:|---:|---:|
| 5 | 1.0492 | 0.4302 | 2.44 |
| 10 | 1.0469 | 0.4374 | 2.39 |

Second-step components include a newly computed witness, proposal, fresh
10k training setup/updates and its gate. Continuation includes only additional
updates from 10k to 20k plus its gate. Both use an additional 10k updates per
role; these are not equal-CPU arms. The first 10k control updates reconstruct
the retained state and are excluded from incremental cost. Input reconstruction,
checkpoint scores, diagnostic repaired LP, I/O and verification are also excluded.
These single-run component sums are not standalone production benchmarks.

## Verification and limits

15 preflight checks passed; four retained first-step policies reproduced before freeze.
All 64 accepted incumbents reconstructed, preserving per-role fallback choices.
256 new asymmetric certificates, 256 saved profiles, 128 selected profiles checked.
1,920,000 updates replayed; 128 independent gate audits; verifier LP calls forbidden.
Independent exchange enumerations: 72,870.
Independent selection and summary arithmetic checks: 2267.
Worker 188.197 s; verifier 192.573 s; total 380.830 s, exit 0.
Python 3.14.6, NumPy 2.5.2, SciPy 1.18.0, one BLAS thread, no allocation tracing.
900-second limit per phase; no hard RSS cap. No model fitting.
Heads-up one-bet river, 96 holdings per role, K=16; every compatible deal included.
No full-range, six-max, live latency, population uncertainty or BB/100 claim.
All 24 predecessor milestones verified unchanged; no adoption, commit or push.

Plan SHA-256: 3bcf4ef5113b41b4acea05c4b1d7fa917166393e28b7b5c2d9440b1e9ac1c3c8

Results manifest SHA-256: 8355465902f0271bd24e3679925f68daa610f9bd79a229d1f39e415ddca70230
