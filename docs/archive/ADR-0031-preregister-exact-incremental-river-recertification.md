# ADR-0031: Preregister exact incremental river recertification

**Status:** Accepted; frozen before the production development run

**Date:** 2026-08-19

## Decision

Test whether sparse range changes can be recertified exactly without repeating
the full river tree and best responses. The frozen configuration is
`experiments/configs/river-incremental-recertification-development-v1.json`,
SHA-256
`6f0c65bf63c06af1f34dae347b2325d1fd338ce4dd1efc35d8c86c37bd85f98a`.
It requests development boards only. Validation and test boards must not be
generated, evaluated, or used to change this rule.

This is the missing control between a cheap loose total-variation bound and a
full current-range best response. It is not approximate range matching. A
compiled policy cache remains bound to its exact source provenance. Every
target evaluation requires a complete source-to-target probability delta whose
source, target, and structure digests are checked before use.

## Exact incremental evaluator

For every source deal, compile probability-free coefficients for:

- fixed-policy utility;
- player 0's root check and bet values plus its fold/call continuation after a
  raise; and
- player 1's fold, call, and raise response values plus the fixed check branch.

The source cache stores the corresponding private-hand counterfactual sums and
their exact best-response maxima. A target delta changes only the two private-
hand aggregates touched by each changed deal. Source contributions are
subtracted for removals; a newly supported deal is compiled under the target
game and the fixed policy's ordinary uniform fallback applies at unseen
information sets. Changed hand maxima and their ancestors are then recomputed.

The implementation exposes no tolerance-based delta omission, nearest-range
hit, or unchecked chained update. Delta discovery scans the complete union of
source and target support once and may then be shared across multiple finite
policy cache entries.

An independent full-tree `evaluate_profile` result remains the correctness
oracle. The maximum absolute error across utilities, both best-response values,
both deviation gains, NashConv, and exploitability must not exceed `1e-10`.
This is numerical identity of two mathematically exact calculations, not a
claim that different floating-point summation orders are bitwise identical.

## Finite policies and range changes

Replace the previous exact-equilibrium source teacher with average policies
from finite DCFR checkpoints 1, 4, 16, and 64. Eight private hands per player
make the full range roughly 64 deals while keeping the independent evaluator
tractable. All four river context families and the sequential bet/raise/call
tree are included.

Each source receives four paired target changes:

1. adversarial support-preserving blocker reweight at player 0, moving at most
   1% root mass and at most 75% of donor mass;
2. the same construction at player 1;
3. replacement of the rarest feasible deal with an unseen player-0 private
   hand at identical mass; and
4. the corresponding unseen player-1 support swap.

The support swap must produce exactly one removed and one added deal, no hidden
reweights, and an information-set hand absent from the source marginal. Its TV
is the removed deal's probability and is not forced to equal the 1% reweight;
the perturbation families are separate transfer axes, not quality-matched arms.

## Timing and gates

Warm hand-rank and interpreter caches before timing. Record five batches and
their per-call median for full evaluation, incremental application, delta
discovery, TV bound, and compiled-cache construction. Tiny operations use
multiple inner repetitions as frozen in the configuration. Report three cost
views:

1. hot incremental application after a verified delta and compiled cache;
2. incremental application plus one delta discovery shared across the four
   finite policy checkpoints; and
3. the same path with one compiled-cache build per source policy charged.

The cache-build view is reported rather than gated because compilation occurs
when a source entry is created and its correct amortization depends on future
reuse count. Also report the conservative no-delta-sharing path, estimated
cache-build break-even reuse count, and a one-batch view charging finite source
DCFR construction. The source solve is common to both full and incremental
evaluation, so that last view is an amortization stress test rather than the
primary head-to-head ratio. No source solve, cache build, delta discovery, or
bound timing may be silently included or excluded from another category.

The production development screen passes only if:

1. maximum absolute evaluation error is at most `1e-10`;
2. summed full median time divided by summed hot incremental median time is at
   least `10x`;
3. the same ratio after charging one shared delta discovery per target is at
   least `5x`;
4. incremental application is faster than full evaluation in at least 99% of
   individual records; and
5. the TV certificate has zero false-positive threshold acceptances against
   exact recertification.

The performance gates characterize this Python reference microgame only. A
pass advances sparse dependency invalidation as an optimized-runtime design;
it does not establish 6-player scalability or authorize approximate neural
leaf reuse.

## Pre-freeze calibration

A distinct small pilot used seed 1901, three development board groups, 12
contexts, two finite checkpoints, and 96 records. Worst absolute error was
`1.07e-14`; hot and shared-delta aggregate speedups were `55.44x` and `27.91x`.
All 96 incremental calls were faster. This pilot selected conservative gates;
it is not part of production evidence and its contexts are not reused by the
frozen seed 20260829 run.

## Dissent protocol

**Confidence:** high that the specialized equations match the current exact
river tree; moderate that sparse dependency cones retain a large advantage in
wider heads-up abstractions; low that the same best-response decomposition
survives multiplayer and dynamic action insertion without materially larger
invalidation cones.

**Opposing evidence:** delta discovery is still linear in range support, new
hands require coefficient compilation, and Python object overhead can either
inflate full traversal or obscure sub-millisecond incremental costs. The
source policies are finite but the game remains heads-up, zero-sum, river-only,
and fixed-action.

**Largest unknown:** whether real public-belief updates remain sparse after
Bayesian action conditioning and whether one delta can be shared across enough
policy/value cache entries to amortize discovery and compilation.

**Cheapest falsification:** run the committed development configuration once,
verify the independent exactness gate first, and compare all three charged cost
views without retuning thresholds or removing support-changing cases.
