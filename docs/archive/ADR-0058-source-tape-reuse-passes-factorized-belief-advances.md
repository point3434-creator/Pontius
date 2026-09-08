# ADR-0058: Source-tape reuse passes; factorized belief advances

**Status:** Implemented; every frozen engineering gate passed

**Date:** 2026-08-19

## Result and provenance

The revealed ADR-0057 audit regenerated all six development groups, 24 source
contexts, 96 support-preserving target ranges, and 1,728 candidate policies.
It compiled 24 source tapes and 96 target-specific controls. No validation or
test context was materialized.

The corrected frozen configuration SHA-256 is
`c602cebfa58ac113d4668bc1abc7da1ffdd285e5fecf981949fc49d5537ccd03`.
The result is
`experiments/results/multiway-source-tape-reuse-audit-v1.json`, SHA-256
`3f1c36b030880526d9144551cd8ebe31fbd881bdeb24c79b3d4797e045c33e53`.
It ran from clean commit
`72ca072cd9af4a556ab2d0cc66bd507dcbf28aff` in 279.952 seconds. Before the
audit, all 329 repository tests passed in 59.493 seconds.

## Exactness verdict

Every frozen correctness gate passed:

- maximum source/target/ordinary evaluation error: `1.95399e-14`;
- maximum reproduction error against the ADR-0056 artifact: exactly `0.0`;
- best-response action mismatches: `0`;
- aggregate, unilateral-Pareto, and coalition-stress label mismatches: `0`;
- policy schema identity: exact;
- range support and structural identity: exact; and
- replay after all other context range/policy calls: numerical error `0.0` and
  literal action-map identity in all 24 contexts.

The source tape is therefore call-order independent for these exact inputs. It
does not accept a nearby range. Each update supplies the complete target root
distribution and candidate policy relative to the immutable source epoch.

## Evaluator economics

| Complete trajectory path | Charged ms | Relative result |
|---|---:|---:|
| Ordinary baseline plus candidate traversal | `48,524.233` | control |
| 96 target compilations plus policy updates | `9,356.704` | control |
| 24 source compilations plus updates | `8,504.023` | `1.1003x` vs target |
| Precompiled source updates | `7,959.796` | `6.0962x` vs ordinary |

Source reuse wins 23 of 24 individual context paths. The minimum context
speedup is `0.9030x`, the median is `1.1091x`, and the maximum is `1.1627x`.
The frozen pooled gate passes, but the one losing context prevents a universal
latency claim.

The component accounting explains the mechanism:

| Component | Total ms | Mean ms |
|---|---:|---:|
| 24 source compilations | `544.227` | `22.676` per context |
| 96 target compilations | `2,001.871` | `20.853` per target |
| Source baseline range updates | `381.689` | `3.976` per target |
| Source combined range/policy updates | `7,578.106` | `4.385` per candidate |
| Target policy-only updates | `7,354.833` | `4.256` per candidate |

Combined source updates are 3.04% slower than target policy-only updates. The
9.11% complete-path reduction comes from eliminating 72 compilations, after
paying for baseline range updates and the denser combined input changes. No
sparse-delta speed claim follows.

Persisting one source tape per context costs 8,844,174 contiguous runtime
bytes. Persisting all four target tapes costs 35,376,696 bytes. The exact ratio
is `0.25`, a fourfold reduction for this topology epoch.

## Primary decision economics

For one DCFR-32 candidate per target, the evaluator-only costs derived from the
recorded components are:

- ordinary baseline plus candidate: `5,142.193` ms;
- target-specific compile plus candidate: `2,416.003` ms;
- one source compile shared across the four targets, plus baseline and
  candidate updates: `1,352.331` ms; and
- precompiled source baseline plus candidate updates: `808.104` ms.

The source-reuse evaluator path is `1.7865x` faster than the target-specific
path for this one-candidate workload. Solver work still dominates the complete
decision, so the quality-rate gain is much smaller.

| Source-tape reuse count | Accepted raw/ms | Ratio to blind DCFR-32 |
|---:|---:|---:|
| Precompiled | `0.00197913` | `1.02065x` |
| 1 | `0.00184817` | `0.95311x` |
| 2 | `0.00191141` | `0.98572x` |
| 3 | `0.00193346` | `0.99710x` |
| 4 | `0.00194468` | `1.00288x` |
| 8 | `0.00196175` | `1.01169x` |

The frozen maximum-eight-reuse gate passes, with observed break-even at four.
That four-reuse margin is only 0.29%, and the precompiled ceiling is 2.06% on
this fixed primary arm. Precompiled source verification beats blind rate in
three of six groups; four-reuse accounting beats it in only two. This is not a
robust grouped online rule, even though the pooled engineering gate passes.

## Density finding

Every target shift changes every positive root outcome: 9 to 24 outcomes per
target. Baseline range-only updates have median dirty-node fraction 58.18%.
Combined candidate updates have median dirty fraction 94.46%, with a median 61
of 72 policy entries changed. Dense execution remains the correct reference
path. Trying to win through dirty queues would attack the wrong bottleneck on
this workload.

## Decision

1. Adopt one source-compiled tape as the exact evaluator oracle for all
   support-preserving range and policy changes within a topology epoch.
2. Invalidate rather than reuse it when public structure changes or a target
   introduces an outcome outside the compiled support. No range-distance cache
   hit is authorized.
3. Treat four observed reuses as a fragile pooled break-even, not a production
   requirement. A native system needs margin, grouped latency evidence, and a
   workload-derived tape lifetime policy.
4. Do not pursue sparse invalidation for dense belief/profile changes. Preserve
   the flat dense path as the exact control.
5. Advance a separately frozen factorized/low-rank belief contraction. Its
   purpose is to remove explicit joint-deal replication inside a tape, not to
   repackage source-tape amortization.
6. The factorized prototype must compare root utilities, every player's
   best-response value and deviation gain, literal response actions, all three
   acceptance labels, time, and memory. Probability reconstruction error or
   value MSE alone cannot pass.
7. Retain coalition computation as an ordinary offline stress teacher. This
   audit did not accelerate it.

The next design should evaluate factor-graph, tensor-train, or another
structured contraction against exact enumeration before selecting a low-rank
family. Card-removal incompatibility and three-way correlation must be explicit
stress axes; a product of marginal ranges is not an adequate control.

## Dissent protocol

**Confidence:** very high in exact source-relative reuse; high in the fourfold
persisted-memory result; moderate in the pooled Python evaluator speedup; low in
the four-reuse total-decision margin.

**Opposing evidence:** support-preserving river updates are the easiest valid
reuse case. Earlier streets can change public cards and legal private support,
forcing recompilation. On the other hand, repeated within-street posterior and
candidate updates can exceed four uses substantially.

**Largest unknown:** whether a compact belief contraction preserves the small
per-seat and pair differences that bind multiplayer acceptance while avoiding
rank explosion from card removal.

**Cheapest falsification:** on widened three-player supports, compare exact
enumeration with structured contraction at increasing retained ranks. If
response actions or strict acceptance labels change before memory and latency
improve materially, reject that representation family.
