# Full-combo direct 002

Same four actual-pot public-range games; full 1081-hand LP versus K=16 compression.
Three check/all-in games and one check/bet14/bet29 game; no duplicate bet actions.

The first attempt passed mathematical verification but observed the Windows venv
launcher instead of its worker. Its memory limits and figures are invalid. This repeat
uses the same algorithms and settings, with a direct interpreter launch and a verified
executing-PID match. A 128 MiB allocation check proves the observer sees worker memory.
All first-attempt bytes are retained below superseded-attempt/; none were rewritten.

## Results

| Case | Sizes | Compressed exploitability | Grouping floor upper | Full exploitability |
|---|---|---:|---:|---:|
| 0 | [76] | 0.00518601392 | 0.00516345602 | 4.95559024e-09 |
| 1 | [14, 29] | 0.0154860201 | 0.0154041189 | not certified |
| 2 | [44] | 0.00170104521 | 0.0016879598 | 4.46439364e-09 |
| 3 | [45] | 0.00374055375 | 0.00372493429 | not certified |

Lower is better. Exploitability is half the unrestricted-response gap, in normalized
chips (payoffs scaled by 10/actual pot). Multiply by actual pot/10 for actual chip units.
Exact rational certificates refer to the binary64 payoff matrix, gap at most 1e-8.

| Case | Compressed + score s | Full solve + certificate s | Full exact bounds s |
|---|---:|---:|---:|
| 0 | 5.412 | 1.373 | 0.179 |
| 1 | 7.596 | 4.604 | 0.359 |
| 2 | 5.572 | 1.481 | 0.192 |
| 3 | 5.601 | 1.387 | 0.167 |

Compressed time includes learner setup, 50000 updates, averaging and final score.
Full time includes dense LP assembly, primal/dual solves and exact original-matrix bounds.
Shared payoff/integer-array preparation and grouping-floor diagnostics are excluded.
This compares operating points, not equal compute or optimally tuned algorithms.
Order alternates by case, with one timing observation. These are not stable speed ratios.

| Case | Sampled worker private MiB | OS worker peak commit MiB | Verified |
|---|---:|---:|---|
| 0 | 1026.3 | 1106.1 | True |
| 1 | 2192.3 | 2220.0 | True |
| 2 | 1082.5 | 1144.6 | True |
| 3 | 1076.2 | 1112.3 | True |

Memory covers the entire worker, including both arms and diagnostics; it cannot be
attributed exclusively to direct or compressed solving. Sample interval 50ms; 3072 MiB
private-memory stop and 120s wall stop per child. This is not a hard memory cap.

## Solver outcomes

- Case 0: full certified; floor certified.
  full LP statuses: [0, 0]; iterations: [1810, 844].
  floor LP statuses: [0, 0, 0, 0]; iterations: [1739, 14, 31, 830].
- Case 1: full not_certified; floor certified.
  full LP statuses: [0, 0]; iterations: [5597, 675].
  floor LP statuses: [0, 0, 0, 0]; iterations: [3451, 42, 1324, 693].
- Case 2: full certified; floor certified.
  full LP statuses: [0, 0]; iterations: [2146, 643].
  floor LP statuses: [0, 0, 0, 0]; iterations: [1700, 20, 35, 554].
- Case 3: full not_certified; floor certified.
  full LP statuses: [0, 0]; iterations: [1903, 445].
  floor LP statuses: [0, 0, 0, 0]; iterations: [1497, 15, 38, 426].

Every original solver status, option, raw solution vector and refusal is retained.
Time-limited or uncertified candidates are not reported as solved equilibria.

## Scope

Full detail means independently represented private holdings, not a full betting tree.
The caller cannot bet after a check or reraise; other legal bet sizes are omitted.
Ranges are those of the early checkpoint, with substantial postflop fallback dependence.
Folded-player cards are not jointly marginalized. No new training or fitted abstraction.
Four known cases establish neither board generalization nor six-max playing strength.
The quality comparison changes representation and solver method together. It establishes
these concrete operating points, not a causal speed effect from representation alone.

## Verification

Three preflight tests cover one/two-size literal bounds, full-hand small LP parity and
all four actual game inputs; four monitor checks exercise allocation, stops and success.
Each successful verifier replays 50000 learner updates, checks all payoff coefficients,
rechecks returned full/group certificates without new LP solves, and repeats engine
settlements. Exact full profiles also face three literal subgame comparisons.
Complete process/verification census: True.
All four full-hand pairs certified: False.
Total bounded campaign time: 83.415s.
All 34 prior milestones preserved. No production changes, commit or push.

Plan SHA-256: 16935aa756141cc276c8ddb311ff53f8ec75beda6b33bffb672b80674e22e615

Results manifest SHA-256: f1931f30d9892b884d9c92ba2aefc607f5c5813c3ae11170dd431f121bb04455
