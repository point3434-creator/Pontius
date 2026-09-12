# Full-hand result assessment

Post-run exact evaluation of every retained primal/dual strategy, including the two
that missed the frozen 1e-8 gap threshold. No new LP solves or relaxed thresholds.

| Situation | Grouped error | Full-hand error | Strict threshold | Grouped s | Full s |
|---|---:|---:|---|---:|---:|
| 1 | 0.00518601392 | 4.95559024e-09 | pass | 5.412 | 1.373 |
| 2 | 0.0154860201 | 1.37087688e-07 | miss | 7.596 | 4.604 |
| 3 | 0.00170104521 | 4.46439364e-09 | pass | 5.572 | 1.481 |
| 4 | 0.00374055375 | 2.16493129e-08 | miss | 5.601 | 1.387 |

Error means half the exact unrestricted-response gap, normalized by 10/actual pot.
Strict pass requires gap <=1e-8, hence error <=5e-9. A missed strict threshold remains
a miss, even when the returned strategy has a small precisely measured error.
The full-hand and grouped strategies were evaluated on the same full payoff matrices.

All four full-hand strategies have less error and took less measured solve time than
the existing 50000-update grouped learner. This compares the concrete LP and learner
implementations, not an inherent speed advantage of full representation over grouping.
Direct LP is the useful reference for this restricted river family; additional repair
tuning has a weaker case until a larger tree makes full solving expensive.

| Situation | Shared preparation s | Sampled worker private MiB | OS peak commit MiB |
|---|---:|---:|---:|
| 1 | 0.387 | 1026.3 | 1106.1 |
| 2 | 0.536 | 2192.3 | 2220.0 |
| 3 | 0.372 | 1082.5 | 1144.6 |
| 4 | 0.379 | 1076.2 | 1112.3 |

Memory covers the entire case worker, including both arms and diagnostic LPs.
Timing excludes shared preparation and grouping-floor diagnostics. One observation
per case; fixed 10s per LP limits, 120s child limit and sampled 3072 MiB private limit.

The first attempt measured the Windows launcher rather than its actual worker; its
memory figures and stop claims are invalid. The corrected repeat verifies executing
PID identity and an observed 128 MiB allocation. Original attempt bytes are preserved.
The coordinator initially misread a complete audit as all strict passes and corrected
that statement after inspecting the individual refusals. This assessment preserves
the two misses and supplies their exact residual errors from retained LP vectors.

## Per-hand tables

Each CSV contains 1081 rows, with both players' ranges, group labels, full and grouped
bet/check probabilities and call probabilities facing each size. Fold is one minus call.
The strict-threshold status is included in every row. Responses on unreachable branches
can differ without changing exploitability. The earlier hand-detail-000.csv export was
interrupted after its first case; the complete current tables are the -v2.csv files.

- [Situation 1](hand-detail-000-v2.csv)
- [Situation 2](hand-detail-001-v2.csv)
- [Situation 3](hand-detail-002-v2.csv)
- [Situation 4](hand-detail-003-v2.csv)

Scope remains check-versus-bet, followed only by fold/call, on four known public
ranges from an early, fallback-heavy checkpoint. All card combinations are represented,
but the full river action tree and multiplayer solving are not. No six-max strength claim.
