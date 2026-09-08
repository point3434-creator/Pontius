# ADR-0032: Exact sparse recertification passes; the next risk is structure

**Status:** Accepted

**Date:** 2026-08-19

## Decision

Accept compiled sparse dependency invalidation as the exact river-cache
recertification control. It removes the measured best-response bottleneck by a
large margin even with unseen-hand support changes and finite DCFR policies.
Do not tune the specialized river equations further or promote a deployment
threshold from this development run.

The next implementation should generalize the same invariant into a compiled
best-response dependency graph, then test it on a wider legal action tree and
structured Bayesian range updates. Only after that transfer should we compare
recertified reuse, selective repair, warm full traversal, and cold solving as
runtime policy arms.

## Frozen production evidence

The implementation and preregistration were committed as `4ca09e7` and
`497d7ea` before the result existed. The frozen configuration SHA-256 is
`6f0c65bf63c06af1f34dae347b2325d1fd338ce4dd1efc35d8c86c37bd85f98a`.

The 3,479,823-byte result artifact is
`experiments/results/river-incremental-recertification-development-v1.json`,
SHA-256
`0daafbc3c241c00befc51f05fa14aaa705a51a880d7b9ae4a5fa2722906b9b9e`.
Its embedded Git state is clean at `497d7ea`. It contains 14 development board
groups, 56 four-family source contexts, 224 range pairs, 224 compiled finite-
policy caches, and 896 recertification records. No validation or test context
was requested or materialized.

Every range change remained mechanically sparse. The 112 blocker perturbation
pairs each reweighted exactly two supported deals. The 112 support swaps each
removed one deal, added one deal containing a previously absent private hand,
and changed no common deal weight.

## Exactness and latency

All preregistered gates pass. Worst absolute disagreement with the independent
full evaluator is `2.31e-14`, far below the `1e-10` gate. Incremental
application is faster in all 896 records; the worst individual speedup is
`48.02x`.

| Cost component | Mean reference latency |
|---|---:|
| Full target policy evaluation and both best responses | 11.1061 ms |
| Exact incremental delta application | 0.1996 ms |
| Complete source-to-target delta discovery | 0.3923 ms per range pair |
| TV exploitability bound | 0.0337 ms |
| Compiled source-policy cache construction | 1.9132 ms |

The aggregate hot exact speedup is `55.652x`. Charging one delta discovery
shared by the four finite-policy checkpoints leaves `37.315x`; pessimistically
charging a separate discovery to every record still leaves `18.766x`. Charging
compiled-cache construction as well leaves `14.313x`. The measured cache-build
break-even is only `0.175` recertifications because one full evaluation costs
far more than compilation plus incremental application.

Finite DCFR construction through checkpoint 64 costs 14,850.2 ms across the 56
sources, or 265.18 ms per source on average. Charging that entire source solve
only to this one reuse batch produces a `0.640x` ratio. This does not reverse
the evaluator comparison—the full path needs the same fixed policy—but it
prevents describing source strategy creation as free. A cache built solely for
a small number of hypothetical future states still requires an explicit reuse
or alternative-solve economic comparison.

## Finite-policy quality

Mean normalized exploitability falls sharply with source DCFR work. Sparse
range damage becomes more visible as solver residual disappears.

| Source checkpoint | Source | Blocker-reweighted target | Unseen-hand support swap |
|---:|---:|---:|---:|
| 1 | 0.068567 | 0.068502 | 0.068578 |
| 4 | 0.009596 | 0.009751 | 0.009621 |
| 16 | 0.001347 | 0.001630 | 0.001379 |
| 64 | 0.000118 | 0.000484 | 0.000153 |

At checkpoint 64, blocker reweighting worsens 103/112 records and adds mean
normalized exploitability `0.000367`; support swaps worsen 100/112 and add
`0.0000349`. This is not evidence that new support is intrinsically safer. The
support swaps move mean TV `0.000652`, versus `0.005535` for blocker reweights,
so the perturbation families are not magnitude matched.

The key separation is now empirical: recertification can be made cheap and
exact, but it only measures a cached policy. It does not repair a strategy whose
quality is inadequate under the target range.

## Bound-first diagnostic

The TV bound remains safe with zero false-positive acceptances. It certifies
44, 237, 392, and 589 of 896 policies at normalized exploitability ceilings
0.1%, 0.5%, 1%, and 2%; exact recertification accepts 307, 485, 595, and 658.

A post-result diagnostic composes the recorded per-record timings without
changing the frozen verdict. Running the bound first and using incremental
exact recertification only on failure changes hot exact-path cost by factors
`0.897x`, `1.133x`, `1.405x`, and `1.982x` at those four ceilings. When delta
discovery is not already available, the corresponding factors are `0.994x`,
`1.274x`, `1.635x`, and `2.522x`.

Thus a bound-first cascade is harmful at a strict 0.1% ceiling but promising at
0.5% and above. These thresholds were inspected after the run; this is an
architecture clue, not a frozen scheduler or deployment rule.

## Consequences

1. Keep exact provenance as the only direct cache-hit identity. A different
   range may use the fixed cached policy only after a stated target-quality
   certificate, not because its distance is small.
2. Preserve separate accounting for policy construction, compiled-cache build,
   delta discovery, cheap bound, exact application, and any repair solve.
3. Replace hard-coded river formulas with a generic bottom-up dependency tape
   whose changed leaves and best-response action flips propagate to ancestors.
4. Add multiple bet and raise sizes before optimizing selective repair. The
   current two-level action tree is too favorable to claim branching-factor
   transfer.
5. Add dense but structured likelihood updates. Real Bayesian conditioning can
   reweight most deals even when its algebra is low-rank; a two-deal sparse
   benchmark is not enough.
6. On the richer tree, compare accept/no-op, bound-first exact recertification,
   affected-cone repair, warm traversal, and cold traversal at equal charged
   time. The frozen river scheduler remains the compute-allocation control.

## Dissent protocol

**Confidence:** high in numerical identity and the reference-kernel speedup;
moderate that dependency invalidation will retain a several-fold advantage
with wider heads-up action trees; low that explicit sparse deltas represent
six-player action-conditioned beliefs.

**Opposing evidence:** full evaluation is deliberately object-heavy Python,
the best-response graph has only two player-decision layers, and every target
changes exactly two joint deals. An optimized flat full traversal will narrow
the ratio, while wider trees and dense belief changes enlarge invalidation
cones.

**Largest unknown:** whether realistic range updates are sparse in a useful
basis—explicit combos, factored player likelihoods, low-rank joint weights, or
cached public-belief sufficient statistics.

**Cheapest falsification:** build one compiled dependency evaluator that is
independent of the river action constants, require exact differential identity,
then cross it with at least three root bet sizes, two raise sizes, and both
sparse and factorized-dense range changes. If its charged speed advantage
collapses, keep the current module as an exact test oracle only.
