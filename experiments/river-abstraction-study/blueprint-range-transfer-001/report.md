# Blueprint range transfer 001

Four first eligible heads-up river starts reached by baseline-000 six-max self-play.
Full 1081-combo public ranges; frozen K=16 size repair; no model fitting.

## Outcomes

| Policy | Mean exploitability (normalized chips) | Accepted |
|---|---:|---:|
| initial | 0.014540815 | - |
| repair | 0.011672018 | 4 |
| continuation | 0.014486314 | 4 |

| Case | Source hand | Board (card ids) | Initial | Repair | Continuation |
|---|---:|---|---:|---:|---:|
| 0 | 2 | [37, 38, 30, 35, 28] | 0.005554376 | 0.004732749 | 0.005423933 |
| 1 | 60 | [29, 1, 44, 32, 8] | 0.015448863 | 0.015176629 | 0.015435868 |
| 2 | 70 | [20, 2, 46, 3, 31] | 0.007915335 | 0.007693065 | 0.007897385 |
| 3 | 90 | [46, 10, 18, 40, 48] | 0.029244687 | 0.019085630 | 0.029188068 |

Exploitability is half the exact unrestricted-response gap in the normalized
heads-up check/half-pot/pot game. Lower is better. The caller is fixed after 50000
incumbent updates; both alternatives must pass the same exact nonworse security gate.
Repair strictly beats continuation in 4/4 cases.
The proposal changes grouping in 4/4 cases.

## Grouping floor intervals

| Case | Original lower | Original upper | Proposed lower | Proposed upper |
|---|---:|---:|---:|---:|
| 0 | 0.005062848 | 0.005062848 | 0.004287186 | 0.004287186 |
| 1 | 0.015349046 | 0.015349046 | 0.015076283 | 0.015076283 |
| 2 | 0.007777328 | 0.007777328 | 0.007558779 | 0.007558779 |
| 3 | 0.029091712 | 0.029091712 | 0.018966035 | 0.018966035 |

These separate representational limits from remaining optimization error.
Each interval combines two primal/dual certificates, checked against the original
binary64 full-game coefficients with exact rationals and gap at most 1e-8.

## Acquisition and range provenance

Capture census: `{'eligible_hands': 4, 'hands': 91, 'hands_with_river_start': 9, 'river_decisions': 25, 'river_start_nodes': 9, 'rivers_dealt': 71}`.
Captured policy decisions by street/status: `{'0:bad': 3, '0:miss': 68, '0:trained': 501, '0:uniform': 129, '1:bad': 1, '1:miss': 24, '2:miss': 25, '3:miss': 25}`.

| Case | Role/seat | Trained observations | Fallback observations | Uniform observations |
|---|---|---:|---:|---:|
| 0 | bettor/1 | 7.794% | 72.641% | 19.565% |
| 0 | caller/5 | 27.729% | 64.847% | 7.424% |
| 1 | bettor/1 | 11.378% | 57.940% | 30.681% |
| 1 | caller/5 | 27.775% | 65.009% | 7.216% |
| 2 | bettor/0 | 19.611% | 64.755% | 15.634% |
| 2 | caller/1 | 3.885% | 68.887% | 27.228% |
| 3 | bettor/1 | 3.793% | 69.812% | 26.395% |
| 3 | caller/3 | 25.000% | 71.577% | 3.423% |

Percentages count combo-by-action observations, not policy queries.

| Case | Seat | Raw zeros | Collapsed | Floor mass added | Lower-floor L1 |
|---|---:|---:|---|---:|---:|
| 0 | 1 | 104 | False | 0.000104 | 0.00020777037 |
| 0 | 5 | 799 | False | 0.000799 | 0.0015951262 |
| 1 | 1 | 154 | False | 0.000154 | 0.00030764458 |
| 1 | 5 | 770 | False | 0.00077 | 0.0015372751 |
| 2 | 0 | 252 | False | 0.000252 | 0.00050336902 |
| 2 | 1 | 142 | False | 0.000142 | 0.00028367568 |
| 3 | 1 | 159 | False | 0.000159 | 0.00031763145 |
| 3 | 3 | 758 | False | 0.000758 | 0.0015133357 |

Raw and effective ranges are retained. Primary floor 1e-6; the 1e-9 diagnostic
compares range vectors only, not alternative solved policies. No fallback or collapsed
range is deleted. Pairwise collision rejection yields 1070190 ordered legal deals per case.
Folded players are not jointly marginalized. These are factorized public ranges.

## Timing and limits

| Case | Range build s | Initial both roles s | Repair plus gate s | Continued plus gate s |
|---|---:|---:|---:|---:|
| 0 | 0.769 | 8.308 | 3.500 | 3.405 |
| 1 | 0.653 | 8.340 | 3.493 | 3.388 |
| 2 | 0.840 | 8.204 | 3.366 | 3.264 |
| 3 | 0.542 | 8.133 | 3.453 | 3.350 |

Continuation stops at the first 250-update block covering measured repair work.
Witness, proposal, setup, updates and averaging count. Gates are excluded from matching
and included in the table. Source range acquisition and exact-kernel setup are shared
preparation. Caller/proposed certificates and verifier replay are research diagnostics.
One timing sample per case; fixed repair-first ordering is not a stable speed benchmark.

Actual source pots/stacks/history are retained but not used as the solved payoff game.
This changes both range source and pool size from the prior 96-hand synthetic studies.
It cannot isolate range shape from compression ratio or imply six-max playing strength.
Four reached states are an exploratory panel, not a broad board-distribution estimate.
Conditional payoff evaluation enumerates all deals, so it has no Monte Carlo hand noise.

## Verification

Eight preflight tests; 23371220 coefficients checked by integer ratios;
860000 learner updates replayed; twelve literal subgame comparisons;
capture repeated exactly; all four ranges replayed and tested with different private cards;
twelve asymmetric certificate pairs and eight gates reverified without new LP solves.
Python 3.14.6; one BLAS thread; no tracing; 1800 seconds per phase; no hard RSS cap.
Worker plus verification: 177.046 seconds, exit 0.
All 32 prior milestone manifests and members preserved unchanged.
No production changes, checkpoint training, commit or push.

Plan SHA-256: 0a2b6be2b87c712dc30a701dc89910675773290d6101fb4592ea06ce9bc55de8

Results manifest SHA-256: cec9d5ef18c7c22922dbd87fc386e4ba2fbf11448e69e55dae3a73caee9ed18d
