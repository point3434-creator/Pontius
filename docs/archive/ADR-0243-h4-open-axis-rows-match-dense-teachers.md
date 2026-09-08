# ADR-0243: h4 open-axis rows match dense teachers

- Status: accepted coefficient control; label-free h32 extraction preflight authorized
- Date: 2026-08-22
- Implements: ADR-0242
- Clean preregistration commit: `a7d052327204e849745dd2b63b0c08e3c0e7c44b`
- Result: `experiments/results/h4-sequence-form-open-axis-v1.json`
- Result SHA-256: `f646af38a3e08fa5f9d926c1ba445633d610d4f8e4d1c7be722a2f3e9e9aae02`

## Result

The frozen h4 differential passed every gate on its first clean invocation in
`2.1124 s`. Both topology arms independently matched their direct dense
source/endpoint teachers.

| Layout | Acting seat | Topology | Row entries | Max profile error | Max fixed-response error | Max gain error |
|---|---:|---|---:|---:|---:|---:|
| full repeated actor | 0 | sequence form; shortcut rejected | 256 | `7.99e-15` | `1.33e-15` | `7.11e-15` |
| post-bet single visit | 2 | behavioral shortcut admitted | 8 | `3.11e-15` | `5.33e-15` | `5.77e-15` |

The acting-seat best-response-invariance error was exactly zero in both arms.
The maximum source zero-sum residual was `3.00e-15`. Every identity remained
below the preregistered `2e-11` ceiling.

The external-axis mutation reversed the explicit hand axes while retaining the
embedded layout axes. The obsolete embedded-key splice then disagreed in all
256 checked entries; the corrected explicit-axis splice selected every action
exactly. This discharges the ADR-0239 defect rather than merely rerunning it.

## Cost and conditioning

The repeated-actor arm retained `12,288` gain-row bytes, reached middle rank
12, and reported `2,484,628` peak numeric bytes. Its response oracle took
`40.96 ms`; coefficient construction took `425.63 ms`, including `393.87 ms`
of contraction and `6.01 ms` of assembly. The six gain rows had numerical rank
6, effective condition number `6.61`, and minimum normalized separation
`0.454`.

The post-bet arm retained `384` gain-row bytes, reached middle rank 12, and
reported `1,899,304` peak numeric bytes. Its response oracle took `4.28 ms`;
coefficient construction took `74.96 ms`, including `69.38 ms` of contraction
and `1.07 ms` of assembly. Its six gain rows had numerical rank 5, effective
condition number `24.04`, and minimum normalized separation `0.144`.

These are sparse CPU h4 measurements. The reported GPU-pool fields are zero by
construction. They do not predict h32 resident GPU latency, memory headroom,
middle rank, response-oracle cost, or the 15-second ledger.

## Interpretation

The finite optimizer result from ADR-0241 now connects to exact open-axis cut
coefficients on both relevant topology classes. Repeated acting decisions
require sequence-form coordinates; the post-bet continuation admits the
cheaper behavioral-axis representation. Exact external posterior hand axes
are part of the coefficient contract.

This accepts the old ADR-0238 cross-payoff algebra only as a row-extraction
primitive, with ADR-0239's embedded-axis splice replaced. It does not revive
the old experiment or authorize a mechanical full-matrix rerun.

## Decision

Authorize one narrow, label-free h32 row-extraction preflight on the accepted
post-bet continuation topology. Before constructing or optimizing a candidate,
the successor must measure exact row identity against an independent accepted
teacher, actual resident GPU construction and marginal pass cost, response-
oracle cost, retained bytes, middle rank, conditioning, GPU-pool headroom, and
the complete conservative 15-second ledger.

The preflight must price only the rows needed for one acting-seat master, keep
all six epigraph families, use exact response signatures without approximate
row deletion, and reserve the independent final-certificate budget. A pass may
authorize a label-free h32 master prototype; it may not open strategy-quality
labels or emit a policy.

## Claims boundary

This is an h4 coefficient-identity control. No strategy-quality, optimizer-
quality, multiplayer-safe, h32-feasibility, deployment, composition, cross-
street, population, or broad poker-strength claim is made.
