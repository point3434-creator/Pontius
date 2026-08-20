# ADR-0104: Interpolation finds safe value; incumbent-relative Pareto is too strict

**Status:** Interpolation accepted as a spare-budget candidate mechanism;
incumbent-relative Pareto stream rejected as the final acceptance contract;
fixed blueprint safety envelope proposed

**Date:** 2026-08-20

## Result

The frozen ADR-0103 audit completed from clean commit `13f400b` with every
mechanism gate passing. The canonical local artifact is
`experiments/results/h32-current-interpolation-audit-v1.json`:

- SHA-256:
  `ba0fdd6ea8dfd67de3f74c9026588d3555525d362a74ad1f03295f35281cb8c0`;
- size: 147,538 bytes;
- config SHA-256:
  `3452e03a9d93c3a13901cc9bb252aa3b50d0297d7f0f3b4f01035d57633254a5`;
  and
- implementation SHA-256:
  `d1756cbe82b6e229a8090216d019381289f51f5f18ef2290dda1c2d735ff6789`.

Measured wall time was 305.348 seconds. All twelve interior policies are
finite and normalized, endpoint error is exactly zero, every target descriptor
and endpoint digest reproduces, and all source/config/resource gates pass.

The frozen sequential incumbent does not improve upon current one. That result
is correct under its preregistered semantics: every interior candidate worsens
seat two relative to current one.

However, interpolation itself succeeds. Alpha 0.50 is safer than the original
blueprint for every seat and has lower NashConv than current one on both local
targets. Balanced remains blueprint-safe at alpha 0.75. The experiment exposes
path dependence in the acceptance rule, not a failure of the candidate
mechanism.

## Exact local interpolation curves

All reductions are normalized NashConv reductions from the target-belief
blueprint. “Blueprint-safe” means aggregate improvement above guard and no
seat's deviation gain above its blueprint value plus the `3e-9` raw guard.

### Balanced local blocker

| Alpha | NashConv | Reduction | Headroom captured | Blueprint-safe | Accepted after current 1 |
|---:|---:|---:|---:|---|---|
| 0.00 | 0.002076554 | +0.000153930 | 6.901% | yes | initialize |
| 0.25 | 0.002053780 | +0.000176703 | 7.922% | yes | no |
| 0.50 | 0.002038411 | +0.000192072 | 8.611% | yes | no |
| 0.75 | **0.002034368** | **+0.000196115** | **8.793%** | **yes** | no |
| 1.00 | 0.002044876 | +0.000185608 | 8.321% | no: seat 2 | no |

### Blocker-heavy local blocker

| Alpha | NashConv | Reduction | Headroom captured | Blueprint-safe | Accepted after current 1 |
|---:|---:|---:|---:|---|---|
| 0.00 | 0.001778102 | +0.000110252 | 5.839% | yes | initialize |
| 0.25 | 0.001769952 | +0.000118401 | 6.270% | yes | no |
| 0.50 | **0.001764632** | **+0.000123721** | **6.552%** | **yes** | no |
| 0.75 | 0.001760142 | +0.000128212 | 6.790% | no: seat 2 | no |
| 1.00 | 0.001756133 | +0.000132220 | 7.002% | no: seat 2 | no |

Alpha 0.50 satisfies the preregistered baseline-safety hypothesis on both
local targets. The predicted common alpha-0.50 final incumbent does not occur
because the frozen stream compares every new vector with current one rather
than the blueprint.

The linear endpoint estimate also understates the balanced safety boundary.
Balanced seat two remains `0.000146` below its blueprint gain at alpha 0.75,
then crosses to `+0.000139` at current two. Blocker-heavy crosses between alpha
0.50 (`-0.0000216`) and 0.75 (`+0.0000417`). Best-response geometry is
nonlinear but remains smooth enough for a coarse bracket to expose useful
interior policies.

## Why the frozen incumbent rejects them

Current one creates excess safety margin for seat two:

- balanced seat-two delta from blueprint: `-0.000483`; and
- blocker-heavy seat-two delta from blueprint: `-0.000143`.

Every positive interpolation step spends some of that margin while improving
aggregate NashConv and usually improving several other seats. Relative to
current one, seat two therefore worsens. The frozen Pareto rule rejects the
candidate even though seat two remains below the certified blueprint cap.

This makes the selected strategy order-dependent. If balanced alpha 0.75 were
considered before current one, it would be accepted as blueprint-safe and have
lower NashConv. Considering current one first blocks it permanently.

Monotone improvement of every deviation-gain coordinate relative to the latest
incumbent is sufficient for safety, but this artifact proves it is not
necessary. It discards safe movements along the interior of the original
constraint set.

## Dense negative controls

No dense interior is aggregate-improving or unilateral-safe. Every one of six
seats remains worse across every coefficient.

| Family | Alpha 0.25 reduction | Alpha 0.50 reduction | Alpha 0.75 reduction |
|---|---:|---:|---:|
| Balanced strength | -0.000986 | -0.001254 | -0.001538 |
| Blocker-heavy strength | -0.001270 | -0.001677 | -0.002119 |

The damage grows monotonically between current one and current two. Behavioral
mixing does not rescue a direction whose entire segment is wrong. The dense
generator decision from ADR-0102 remains unchanged.

## Frozen hypotheses

The preregistered hypotheses resolve as follows:

1. alpha 0.50 baseline-safe on both local targets: **true**;
2. frozen interpolation stream improves its current-one incumbents on both:
   **false**;
3. no dense interior unilateral accept: **true**;
4. same interior final incumbent on both local targets: **false**;
5. frozen four-target stream improves total current-one quality: **false**;
   and
6. alpha 0.75 unsafe on both local targets: **false**; balanced remains safe.

The failed stream hypotheses remain failed. The baseline-envelope analysis
below is an explicitly post-run semantic diagnostic, not a rewritten result.

## Fixed-envelope diagnostic

Consider a different acceptance contract:

1. freeze per-seat caps at the certified blueprint deviation gains plus guard;
2. reject every candidate outside any cap; and
3. among feasible candidates, retain the lowest-NashConv policy.

Replaying the already measured candidates selects:

- balanced local: alpha 0.75;
- blocker-heavy local: alpha 0.50; and
- both strength targets: blueprint.

Total normalized NashConv falls from the current-one result `0.028178213` to
`0.028122558`. Safe reduction from the four blueprints rises from
`0.000264181` to `0.000319837`, a 21.07% increase, with no blueprint cap
violation.

A single fixed alpha 0.50 on both local targets captures nearly all of that:
total safe reduction `0.000315794`, 19.54% above current one. This fixed-alpha
calculation does not use a target selector.

The fixed envelope is order-independent for a fixed candidate set when its
scalar objective has a deterministic tie rule. It preserves the declared
opponent-specific safety contract while allowing safe use of slack created by
earlier candidates. It is not coalition safety.

## Quality per millisecond and spare compute

The twelve new exact reads cost 299.783 seconds; all other audit work cost
5.565 seconds. The complete five-candidate precompiled portfolio bill is
697.853 seconds across four targets.

A post-run fixed-alpha-0.50 bill charges two warm steps plus one alpha-0.50 read
per target. It costs 299.472 seconds for normalized safe reduction
`0.000315794`, or `1.054e-9` per millisecond.

Current one remains the quality-per-millisecond leader:

- cost: 200.121 seconds;
- safe reduction: `0.000264181`; and
- rate: `1.320e-9` per millisecond.

Alpha 0.50 adds `0.000051612` safe quality at about 99.351 additional seconds,
a lower marginal rate near `5.20e-10` per millisecond. This creates a measured
compute ladder:

1. **tight budget:** one warm step plus current-one verification;
2. **spare budget:** second warm step, construct alpha 0.50, and verify it;
3. **larger offline budget:** discrete coefficient portfolio under the fixed
   safety envelope.

This is the first direct implementation answer to the project's spare-compute
question. More compute improves the same decision, but only through a new
candidate direction and a less path-dependent safety contract—not by blindly
continuing CFR.

## Correctness and resource result

All frozen mechanism gates pass:

- maximum exact evaluation: 29.136 seconds;
- maximum target compilation: 66.223 milliseconds;
- maximum zero-sum residual: `8.93e-15`;
- maximum host numeric estimate: 1.487 GB;
- maximum GPU pool: 2.127 GB; and
- exact 435/311 terminal-batch identity.

## Decision

1. Retain current one as the tight-budget candidate and best measured verified
   quality-per-millisecond point.
2. Retain fixed alpha 0.50 as a validated spare-budget candidate. It is
   blueprint-safe on both local targets and adds absolute quality at a lower
   marginal rate.
3. Reject incumbent-relative Pareto monotonicity as the only acceptance
   contract. It is safe but path-dependent and unnecessarily conservative.
4. Preregister a zero-new-evaluation acceptance-semantics replay over the full
   ADR-0099/0101/0103 candidate corpus. Compare incumbent-relative Pareto with
   a fixed blueprint envelope and verify order invariance, cap compliance, and
   deterministic tie behavior.
5. If the fixed envelope passes that audit, make it the policy-delta verifier's
   acceptance customer. Preserve the full per-seat vector in every cache and
   certificate.
6. Keep the dense shifts on the generator-research path. Interpolation between
   two harmful endpoints is now empirically rejected.
7. Do not fit alpha 0.75 balanced versus alpha 0.50 blocker-heavy as a target
   selector. Alpha 0.50 is the only common fixed coefficient supported here.

## What this establishes—and what it does not

Behavioral interpolation extracts additional blueprint-safe value from sharp
warm policies in both local target families. The exact result also shows that
the previous sequential Pareto rule confounded “no worse than the certified
blueprint” with the stronger requirement “no coordinate ever worsens from the
latest incumbent.”

It does not establish that blueprint-relative caps are sufficient under
coalitions, that alpha 0.50 transfers across boards, or that the current exact
teacher is online-ready.

## Dissent protocol

**Confidence:** very high in the measured interpolation curves and the logical
path-dependence diagnosis; high that a fixed-envelope replay is the correct
next audit; moderate that blueprint-relative caps are the right eventual
runtime contract.

**Opposing evidence:** an incumbent-relative cap protects every improvement
already earned. Returning toward a blueprint cap can increase exploitability
to a specific opponent even while lowering total NashConv. Some applications
may prefer that stronger monotonic guarantee despite its opportunity cost.

**Largest risk:** weakening the acceptance semantics in pursuit of a small
aggregate gain without modeling coalitions or the operational cost of an
opponent-specific regression.

**Cheapest falsification:** replay both contracts over every exact candidate
vector already stored, under multiple candidate orders, with zero new strategy
evaluation. The fixed envelope must never breach a source cap and must return
the same optimum independent of order.
