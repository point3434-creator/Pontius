# ADR-0030: Recertification, not warm solving, is the range-reuse bottleneck

**Status:** Accepted; warm-prior promotion deferred

**Date:** 2026-08-19

## Decision

Retain exact-provenance-only strategy hits and structural-only topology/policy
hints. Accept the preregistered warm-start screen as a formal development pass,
but do not freeze its checkpoint-four prior for reserved evaluation. The
recorded checkpoint-zero control is both stronger and cheaper: with an exact
source strategy, current-range recertification usually makes additional DCFR
work unnecessary.

The next range-reuse experiment must replace the optimistic exact source with
finite cached policies and attack recertification cost directly. Build a
delta-aware exact control that caches per-deal evaluation and best-response
dependencies, invalidates only the changed range contributions, and recomputes
the affected information-set/ancestor cone. Compare it bit-for-bit with a full
current-range best response before considering approximation.

Make C3's exact river/cache work the active checkpoint. C2's reference solvers
and frozen scheduler remain controls; its external-sampling and generic tree-
mutation backlog resumes against a more representative reduced-hold'em tree.

## Production evidence

The development implementation and frozen configuration were committed as
`f514720` before the production artifact existed. The 10,840,740-byte artifact
has SHA-256
`470d54d8f10bdd7e02c2f607da7dbe50ee03c91248e05558ac30042a096b78a1`.
It contains 19 board groups, 76 source contexts, 152 range pairs, six arms per
pair, and 8,208 trajectory records.

All 152 range-different lookups are `structural_only`; none returns a directly
deployable strategy. The perturbations have mean root joint TV 0.924% and
median selected-hand conditional TV 19.0%. Maximum conditional TV reaches
66.67%.

The exact source and target equilibrium policies can still be very different
locally: maximum information-set policy TV has median `0.333`, 95th percentile
`1.0`, and maximum `1.0`. Nevertheless, the fixed source policy's target
normalized exploitability has median `0.000364`, mean `0.000618`, 95th
percentile `0.002328`, and maximum `0.003507`. Large local strategy distance
therefore does not by itself imply large root harm, and small root TV does not
imply local strategy stability.

## Frozen checkpoint-four screen

Four training folds select a warm prior and the fifth evaluates it. Three folds
select `warm_span_0_3`; two select `warm_span_1`. All frozen gates pass:

| Fold | Targets | Selected prior | Raw uplift over cold | Cold residual removed | Charged rate uplift |
|---:|---:|---|---:|---:|---:|
| 0 | 24 | 0.3 span | 59.101 | 96.20% | 28.10% |
| 1 | 40 | 0.3 span | 32.495 | 91.24% | 8.70% |
| 2 | 40 | 0.3 span | 43.026 | 96.00% | 23.49% |
| 3 | 32 | 1.0 span | 15.751 | 89.68% | 7.17% |
| 4 | 16 | 1.0 span | 49.030 | 95.38% | 31.55% |

Aggregate fold-local final exploitability is `11.441` versus `210.844` cold,
removing 94.574% of cold residual above the exact targets. One-shot charged
reduction/ms is `1.23698` versus `1.04274`, an 18.628% improvement, at exactly
the same 138,432 deterministic solver state visits. All-development selection
chooses the 0.3-span prior.

## Stronger recorded control

The source strategy at checkpoint zero, after one exact current-range
recertification and before any DCFR step, has aggregate exploitability `10.409`.
This is lower than both the fold-selected checkpoint-four result (`11.441`) and
the all-development 0.3-span checkpoint-four result (`11.214`). Additional
warm-start solving slightly damages the already strong cached policy on average.

A pure lookup-plus-exact-recertification path costs 409.730 ms across all 152
pairs and achieves reduction/ms `3.02872`, versus 997.874 ms and `1.04274` for
cold checkpoint four: a 190.46% rate improvement while removing 95.06% of the
cold residual. This is a development diagnostic, not a post-hoc frozen rule.

The critical caveat is source construction. Exact source teachers cost 106.493
ms on average. That cost is excluded only because a cache lookup assumes the
source solve is already sunk; charging it to one reuse destroys the advantage.
A production claim therefore requires finite source policies and explicit
reuse/amortization counts.

## Certificate result

The two-player TV exploitability certificate is safe but loose. It costs only
0.0227 ms on average versus 2.526 ms for full exact target recertification, and
it produces zero false positives. At normalized exploitability ceilings of
0.1%, 0.5%, 1%, and 2%, it certifies respectively 0, 3, 10, and 43 of 152
pairs. Exact recertification passes 115, 152, 152, and 152 pairs.

Among nonzero actual harms, the certificate-to-actual ratio has median 40x.
A bound-first/full-exact-fallback pipeline is slower than full exact at the
0.1% ceiling, saves only 1.02% at 0.5%, 5.33% at 1%, and 25.72% at 2%. The
global payoff-span bound is a safe veto/acceptance check, not yet the efficient
recertifier we need.

## Consequences

Do not spend the next milestone tuning warm-prior strength. The larger prize is
an incremental current-range certificate between the 0.023 ms loose bound and
the 2.526 ms full best response. Preserve exact provenance as the only direct
hit. Treat finite-policy quality, source cost amortization, changed-support
cases, and wider action trees as required transfer axes.

## Dissent protocol

**Confidence:** high that exact cache safety and the development comparison are
correct; moderate that delta-aware exact recertification can exploit sparse
range changes; low that the exact-source advantage survives finite cached
policies and larger action trees.

**Opposing evidence:** the experiment gives the cache an exact equilibrium,
perturbs only two existing deal weights, and excludes its 106.5 ms mean source
construction as sunk work.

**Largest unknown:** how source residual, perturbation sparsity, and dependency-
cone size interact in a realistically under-solved tree.

**Cheapest falsification:** cache finite source DCFR checkpoints, apply the same
paired changes plus support-changing shocks, and require an incremental
recertifier to match full target exploitability exactly while improving charged
latency.
