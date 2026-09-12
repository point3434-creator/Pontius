# Witness repair regression diagnostic 001

Retrospective investigation of all 96 cases in the pilot and confirmation.
Outcomes were known before design. This does not validate a new acceptance
rule on untouched boards. No production source or adopted policy changed.

## Measured effects

Exploitability in chips, lower is better. All methods use saved 10k policies.
Each gate independently selects the original or repaired policy per seat.

| Panel | Bet | Original | Unguarded repair | Structural | Floor | Security |
|---|---:|---:|---:|---:|---:|---:|
| confirmation | 10 | 0.024700495 | 0.015332533 | 0.016259093 | 0.014548103 | 0.014548103 |
| confirmation | 5 | 0.012072532 | 0.009133265 | 0.009229525 | 0.008797505 | 0.008793280 |
| pilot | 10 | 0.022517920 | 0.013802497 | 0.017533991 | 0.013790854 | 0.013775367 |
| pilot | 5 | 0.011856035 | 0.007603586 | 0.007563924 | 0.007075983 | 0.007075983 |

| Panel | Bet | Gate | Accepted seats | Actual worse cases | Floor worse cases |
|---|---:|---|---:|---:|---:|
| confirmation | 10 | floor | 60 | 0 | 0 |
| confirmation | 10 | security | 60 | 0 | 0 |
| confirmation | 10 | structural | 50 | 0 | 0 |
| confirmation | 5 | floor | 57 | 1 | 0 |
| confirmation | 5 | security | 57 | 0 | 0 |
| confirmation | 5 | structural | 53 | 1 | 0 |
| pilot | 10 | floor | 28 | 0 | 0 |
| pilot | 10 | security | 27 | 0 | 0 |
| pilot | 10 | structural | 22 | 1 | 0 |
| pilot | 5 | floor | 28 | 0 | 0 |
| pilot | 5 | security | 28 | 0 | 0 |
| pilot | 5 | structural | 25 | 0 | 0 |

## Mechanism

For each seat, fixed-witness improvement minus opponent-adaptation penalty
equals the change in the certified own-value upper endpoint, exactly.
Both interval endpoints classify material minimax losses. The merge is also
re-evaluated under the repaired game's witness while preserving its original
split membership. This separates a free-looking merge from its later cost.

| Panel | Bet | Damaged seats | Free old merge | Costly new merge | Old policy lost |
|---|---:|---:|---:|---:|---:|
| confirmation | 10 | 3 | 3 | 3 | 3 |
| confirmation | 5 | 5 | 5 | 5 | 5 |
| pilot | 10 | 2 | 2 | 2 | 2 |
| pilot | 5 | 3 | 3 | 3 | 3 |

## Worst raw cases

| Panel | Bet | Case | Seat | Fixed gain | Adaptation | New merge cost |
|---|---:|---|---:|---:|---:|---:|
| confirmation | 10 | b15-p0-uniform | 0 | 0.011605492 | 0.037748994 | 0.048389000 |
| confirmation | 10 | b15-p0-uniform | 1 | 0.005351041 | 0.000538319 | 0.000643756 |
| confirmation | 5 | b03-p0-uniform | 0 | 0.024294857 | 0.024294857 | 0.000000000 |
| confirmation | 5 | b03-p0-uniform | 1 | 0.005110075 | 0.010708165 | 0.019291209 |
| pilot | 10 | b00-p0-polarized | 0 | 0.002765765 | 0.002765765 | 0.000000000 |
| pilot | 10 | b00-p0-polarized | 1 | 0.000000000 | 0.000000000 | 0.000000000 |
| pilot | 5 | b07-p0-uniform | 0 | 0.008436708 | 0.007536002 | 0.000000000 |
| pilot | 5 | b07-p0-uniform | 1 | 0.002947766 | 0.017275693 | 0.049147292 |

## Gate interpretation and limits

Structural checks preserve feasibility of the old asymmetric optimal policy.
They do not ensure that the new finite-iteration policy reaches its quality.
Floor checks compare conservative certificate endpoints, protecting the group
class while leaving finite-iteration error unguarded.

The security gate compares exact worst-case values of the saved policies.
With L(x)=min_y V(x,y) and U(y)=max_x V(x,y), exploitability is (U-L)/2.
Accepting bettor L only upward and caller -U only upward cannot increase
exploitability in this known two-player one-bet game. Every mixed profile was
checked by the existing exact evaluator. Equality is allowed; failures fall
back independently per seat. No acceptance threshold was tuned.

This guards the saved strategy, not every strategy its grouping could learn.
The exact evaluator uses the full known game; sampled, approximate, multiway
or online deployments do not inherit this guarantee automatically.
A gate belongs in the research harness before deployment. No gate is adopted.

## Verification and retention

Five analytic controls and one already-observed pilot-cell preflight passed.
384 asymmetric certificates and 288 composed profiles checked.
192 exact witness decompositions; no new LPs, model fits or training updates.
Independent retained arithmetic checks: 2496.
Diagnostic completed in 114.080 seconds, exit 0.
Python 3.14.6, NumPy 2.5.2, SciPy 1.18.0; one BLAS thread.
600-second worker limit; no hard memory cap. No independent cold review.
All 22 previous milestone manifests and members verified unchanged.
No production edits, adoption, commit or push.

Plan SHA-256: 77cd26fa6fe558a2f8a0c077da03b563fd2ec087536d1c58da2cdd0c3b1dcb64

Results manifest SHA-256: f21a3500417f9ba670c4d40fbdadc9c0c4b95093c314608ff955419c6e481fa4
