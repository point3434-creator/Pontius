# ADR-0053: Multiway contract passes; explicit joint enumeration is teacher-only

**Status:** Implemented; revealed engineering calibration passed

**Date:** 2026-08-19

## Result

The ADR-0052 contract is implemented in `MultiwayRiverHoldem` and the generic
shared-information coalition evaluator. The game supports two through six
players, exact correlated joint ranges, independent marginal construction with
card removal, cyclic one-bet response order, multiway ties, and separate
structure/range provenance. Exact unilateral and pair-coalition metrics remain
separate, as do unilateral-Pareto and coalition-stress acceptance labels.

Twenty-four contract tests pass. They cover all thirteen reachable three-player
terminal paths, an independent contribution audit, two-to-six-player action
order, information hiding, conditional ranges, stochastic pure-policy best
response enumeration, singleton-team equivalence, pair-team enumeration, both
generic dependency tapes, and positive payoff scaling. The implementation was
committed as `d808425` after the frozen contract commit `f66887f`.
The complete repository passes 313 tests in 50.440 seconds.

The reproducible engineering calibration uses
`experiments/configs/multiway-river-cost-calibration-v1.json`, SHA-256
`1e53695f1aaf933d6cea557be1d010285df763bc413c90e31159bbdd59236de6`.
It is explicitly revealed calibration, not a preregistered strategy test. The
result is
`experiments/results/multiway-river-cost-calibration-v1.json`, SHA-256
`d0f74bb9b77766aa233f6cc6ccd16533d6f0242e2e7a59b367ea83063f833e20`.

The calibration's maximum exact evaluation error is `9.32588e-15`, with zero
literal best-response action mismatches and topological dependencies throughout.

## Cost boundary

The calibration gives every seat a disjoint set of `h` private hands, so all
`h^3` three-player joint deals survive card removal. Timings are hot-cache
Python medians on this machine. `Full` is exact candidate profile evaluation,
`team` evaluates all three pair coalitions, and `hot` is dense policy-tape
candidate evaluation after compilation.

| Hands/seat | Joint deals | Tree states | Full ms | Team ms | First DCFR iteration ms | Compile ms | Hot ms | Full/hot |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 1 | 25 | 1.399 | 1.434 | 0.526 | 1.180 | 0.242 | 5.785x |
| 2 | 8 | 200 | 10.411 | 10.903 | 3.804 | 7.955 | 1.779 | 5.853x |
| 3 | 27 | 675 | 35.802 | 36.565 | 12.999 | 25.426 | 5.751 | 6.226x |
| 4 | 64 | 1,600 | 85.520 | 85.645 | 30.972 | 62.444 | 13.889 | 6.157x |
| 5 | 125 | 3,125 | 169.606 | 172.183 | 61.152 | 125.333 | 26.270 | 6.456x |
| 6 | 216 | 5,400 | 306.148 | 307.602 | 111.737 | 216.880 | 46.627 | 6.566x |

Tape storage rises from 22,012 bytes at one deal to 4,395,037 bytes at 216
deals. Both tree states and reference latency are nearly linear in enumerated
joint deals. The apparent input parameter is hands per seat, however, so the
representation is cubic already at three players and would be exponential in
player count. It is an exact teacher representation, not a route to six-player
runtime play.

## Decision

1. The exact contract passes and is large enough for a grouped three-player
   development workload at two or three hands per seat.
2. Dense policy-tape reuse advances. It is 5.79x-6.57x faster hot. Even the sum
   of separate median compilation and one hot candidate is slightly below one
   ordinary candidate evaluation in every calibrated row, although that
   approximate sum is not a synchronized latency benchmark.
3. Coalition evaluation currently costs roughly another complete unilateral
   evaluation. It remains a required offline label and a separately charged
   strict acceptance arm; it is not silently included in the hot unilateral
   tape claim.
4. Explicit joint-deal enumeration is permanently rejected as the scaled
   architecture. A later scalable representation must contract factorized or
   low-rank beliefs without materializing their full Cartesian product. The
   exact game becomes its oracle.
5. The next experiment will freeze a grouped three-player range-shift matrix.
   It will compare blind full search, aggregate exact acceptance, per-player
   unilateral-Pareto acceptance, and pair-coalition-stress acceptance while
   separating candidate solve, tape compilation, hot evaluation, and coalition
   costs. No scheduler is fitted.

## What this changes

The first multiplayer bottleneck is not action branching. With one binary bet,
chance/belief enumeration already dominates and grows as the product of range
support sizes. This moves factorized public-belief contraction ahead of native
action-width specialization, but only after the small exact matrix establishes
whether search plus the stricter acceptance labels has useful strategy value.

## Dissent protocol

**Confidence:** high in exact correctness and the qualitative joint-support
scaling result; moderate in the timing ratios; low that two-to-three hands per
seat expose all important multiplayer strategic effects.

**Opposing evidence:** card removal reduces many realistic Cartesian products,
and optimized native contractions may change constants radically. Also, the
one-bet tree makes the hot tape unusually regular.

**Largest unknown:** whether aggregate NashConv improvements survive per-seat
and pair-coalition non-worsening constraints often enough to justify online
search.

**Cheapest falsification:** the next small grouped matrix. If full warm search
rarely improves the baseline, or strict labels reject nearly every genuine
improvement, representation optimization is premature and the game topology
must become richer before further kernel work.
