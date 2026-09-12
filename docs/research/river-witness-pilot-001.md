# Witness grouping fresh-board pilot: witness-pilot-001

Completed one approved invocation: 48/48 cases, eight fresh boards, three hand pools
per board, 96 holdings per seat, and uniform/polarized range regimes. There was
no retry, missing case, parameter change or post-result panel selection. This is
a balanced descriptive pilot of a fixed oracle-assisted representation method.

## Main result

Lower grouping floor is better. The floor is the minimum full-hand exploitability
achievable with the specified groups in this one-bet heads-up river game. It is
not a win rate or BB/100, and is not a claim about a trained deployed strategy.
Numbers below are midpoints of retained numerical intervals, in game chips.
All compressed candidates use the same occupied group counts within each case.

| Method | Mean floor | Candidate reduction | Candidate lower/higher/overlap |
|---|---:|---:|---:|
| uniform_equity_200 | 0.007981487 | 75.68% | 47/1/0 |
| range_equity | 0.006081930 | 68.08% | 45/3/0 |
| range_response | 0.005289302 | 63.30% | 44/4/0 |
| witness_advantage | 0.001941291 | - | - |
| Full-hand control | approximately zero | not a compressed control | 0/41/7 |

The primary comparison is range_equity; range_response is secondary. The mean
is equal-weight over the eight boards after averaging pools and regimes. The
full-hand numerical mean midpoint is 4.14e-17 chips; no percentage is meaningful
against that approximately zero reference. Seven candidate intervals overlap
that control numerically, which does not assert exact mathematical equality.

## Board and pool sensitivity

Every board mean favors the candidate against all three compressed controls.
Negative deltas favor the candidate. Pool SD describes variation among three
pool means on that board, each averaging the two regimes. It is not a standard
error or confidence interval. Boards are numbered from zero as in the bound plan.

| Board | Cards | Candidate | Delta equity | Delta response | Pool SD equity |
|---|---|---:|---:|---:|---:|
| 0 | 4h 8d Th Qs Kd | 0.0022894 | -0.0066955 | -0.0051498 | 0.0009222 |
| 1 | 4h 7h Td Jd Kc | 0.0016387 | -0.0053621 | -0.0029877 | 0.0022787 |
| 2 | 3c 5d 7s 9s Ks | 0.0002421 | -0.0027383 | -0.0018300 | 0.0008157 |
| 3 | 2d 3c 9c Qs Ac | 0.0003304 | -0.0026800 | -0.0016084 | 0.0005237 |
| 4 | 4s 8h 8s 9h Ac | 0.0023397 | -0.0032245 | -0.0024616 | 0.0035446 |
| 5 | 4h 5c 5s Ks Ad | 0.0032961 | -0.0036354 | -0.0041026 | 0.0024090 |
| 6 | 6d 6h 6s 7c 9h | 0.0016490 | -0.0043101 | -0.0033767 | 0.0019890 |
| 7 | 3h 4d 4h Td Ts | 0.0037450 | -0.0044793 | -0.0052673 | 0.0015921 |

Primary between-board SD: 0.001381380 chips.
Leave-one-board-out primary mean deltas range from -0.004349305 to -0.003775654.
Every such mean remains negative. This shows that removing any single board
does not reverse the mean result on this panel; it is not population inference.

## Regimes and texture categories

| Regime | Candidate | Range equity | Range response | Lower vs equity/response |
|---|---:|---:|---:|---:|
| polarized | 0.0011107 | 0.0067662 | 0.0051515 | 24/24 of 24 |
| uniform | 0.0027718 | 0.0053977 | 0.0054271 | 21/20 of 24 |

All 24 polarized cases improved against both range controls. Uniform cases
account for all regressions. This is an observed subgroup pattern, not a newly
selected headline or a causal claim about polarization.

| Texture | Candidate | Delta equity | Delta response |
|---|---:|---:|---:|
| multiple-pairs-or-trips | 0.0026970 | -0.0043947 | -0.0043220 |
| one-pair | 0.0028179 | -0.0034299 | -0.0032821 |
| unpaired-flush-possible | 0.0002862 | -0.0027091 | -0.0017192 |
| unpaired-no-flush | 0.0019640 | -0.0060288 | -0.0040687 |

## Retained regressions

Every case worse than at least one compressed control appears below. A negative
entry in another column means that same case improved against that control.
These five cases were retained and contribute to the overall result.

| Case | Delta uniform equity | Delta range equity | Delta range response |
|---|---:|---:|---:|
| b00-p0-uniform | -0.005430454 | -0.005619505 | 0.001490533 |
| b02-p0-uniform | -0.001182592 | -0.001786207 | 0.000470952 |
| b04-p2-uniform | -0.000541225 | 0.000740219 | 0.000567717 |
| b05-p1-uniform | 0.000869983 | 0.003380819 | 0.000810516 |
| b06-p2-uniform | -0.000075382 | 0.000330926 | -0.000487833 |

## Run and verification

Worker: 191.524 s, including fresh witness-bank generation.
Whole invocation including parent validation: 249.077 s.
The worker limit was 1,200 s; parent validation and I/O were outside that bound.
Python 3.14.6, NumPy 2.5.2, SciPy 1.18.0, one sequential worker, one BLAS thread.
No RSS cap or measured peak-memory claim. No allocation tracing was enabled.
The 480 planned LP calls produced 240 certified floors. Each LP retained the
five-second and 10,000-iteration bound. Both worker and parent exited zero.

The frozen parent independently reconstructed every game, input, control bank,
feature/group proposal and certificate before writing a complete summary and
manifest. A separate read-only audit verified all 54 manifest members, 240 floor
interval identities, 480 asymmetric gap records, 192 case comparisons, and all
board/pool/regime/texture/leave-one-out aggregates, with no additional LP calls.
Maximum recorded asymmetric certificate width: 1.703e-15 chips.
These are numerical bounds on binary64 payoff coefficients, not sampling error.
The post-run audit does not independently reimplement the card evaluator.

## Interpretation and limits

The earlier development improvement persists across every fresh board average
in this panel and most individual cases. This strengthens the case for retaining
decision-relevant opponent-response information in hand grouping. The frozen
method used exact-game and other solved opponent witnesses; this result does
not show that a cheap or learned feature generator can obtain the same benefit.
There was no equal-compute comparison even though fresh witness cost is included.
The eight deliberately balanced boards, two range regimes and 96-hand pools
do not establish all-board significance, full-pool behavior, or six-max strength.
The previously fresh boards are now observed and must not be reused as unseen
holdout evidence for a method tuned on this result. No new test is authorized.

## Retention and authority

Approval was recorded verbatim as "I approve", bound to plan SHA-256:
535a3fa5b4d55d8bc6cc29763c63b5ab41f89cf0ea190bca90f9c00a5a8c9d2c.

[Plan and review](river-witness-pilot-r001/disposition.md).
[Invocation evidence](river-witness-pilot-r001/invocation-001/verification.json).
[Retained summary](../../experiments/river-abstraction-study/witness-pilot-001/summary.json).
[Milestone manifest](../../experiments/river-abstraction-study/witness-pilot-001/milestone-manifest.json).

Original output: D:/Pontius-training/river-abstraction-study/witness-pilot-001.
A separate immutable milestone copy retains all outcomes and audit evidence.
Prior milestones and frozen packet bytes remain unchanged. No commit or push
was authorized or performed.
