# ADR-0166: A prepared street fits two atomic certificates after one warm step

- Status: accepted result
- Date: 2026-08-21
- Implements: ADR-0165
- Result: `experiments/results/h32-atomic-street-scheduler-v1.json`

## Result

All nineteen frozen integrity gates passed from clean preregistration commit `fbab388`. Both prepared balanced h32 target contexts executed one actual six-seat resident DCFR step, extracted the resulting current policy, built the deterministic six-atom library, and ran the fixed deadline scheduler.

The live one-step candidates reproduced retained `search_current1` within `2.57e-16` maximum probability error and `1.06e-18` mean infoset total variation. All selected information keys matched ADR-0160. Four attempted response prefixes reproduced retained labels within `2.25e-15`, with exact stop and work identity.

No complete strategy-quality evaluator ran. Packing was not invoked. Both trials emitted the immutable blueprint.

## Street ledgers

| Component | Local blocker | All-seat strength |
|---|---:|---:|
| Resident warm step | 11,504.59 ms | 11,616.49 ms |
| Manifest plus six atomic policies | 191.66 ms | 210.41 ms |
| First certificate, acting seat 0 | 372.43 ms | 346.88 ms |
| Second certificate, acting seat 1 | 1,033.84 ms | 602.30 ms |
| Clock before emission reserve | 13,114.63 ms | 12,789.10 ms |
| Fixed emission reserve | 1,000.00 ms | 1,000.00 ms |
| Hard ledger | 14,114.63 ms | 13,789.10 ms |
| Margin below 15 seconds | 885.37 ms | 1,210.90 ms |

Both acting-seat-0 atoms completed the fixed envelope. Both acting-seat-1 atoms reproduced their retained blueprint-cap stops. After the second result, fewer than the frozen 1,250 ms remained before the 14,000 ms certification cutoff, so the scheduler correctly declined to start acting-seat 2. There were four attempted and four usable certificates, with no late result.

Peak CuPy pool total was 7,894,818,816 bytes and physical free memory never fell below 7,259,291,648 bytes. The full audit completed in 57.04 seconds including off-clock construction for both trials.

## Decision

Accept the prepared-context capacity measurement: on these two frozen h32 trials, one complete resident warm step plus deterministic atom construction plus two incremental certificates fits inside 15 seconds with the fixed 1-second emission reserve.

The solver spine is now operationally coherent:

1. shared topology and two immutable belief contexts remain resident;
2. allocator scratch is trimmed before street readiness;
3. one full resident warm step creates the source-relative bundle;
4. deterministic atomization costs about 0.2 seconds;
5. the deadline guard admits two exact atomic certificates; and
6. the immutable blueprint remains the fail-closed output.

Search consumes approximately 77% of the total decision boundary and is now the dominant adjustable bill. Response certification is no longer the primary latency bottleneck on this workload.

## Limits and next question

The 1-second emission allowance remains reserved rather than directly measured, and two one-shot targets cannot establish a latency distribution. Therefore deployment remains unauthorized.

This result also says nothing about whether the two certifiable atoms capture useful value, whether acting-seat order is optimal, or whether packing is worthwhile. Those require a new explicit strategy-quality or bounded-oracle question. No atom may be selected or composed from this systems result.

The next systems-only alternative, if strategy quality remains frozen, is to instrument actual state-ingest, synchronization, and action-emission tails. The next research alternative is a separately preregistered value-capture audit over retained labels, with packing still subject to exact union recertification.
