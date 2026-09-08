# ADR-0033: Flat dependency-tape and finite-policy acceptance contract

**Status:** Accepted for implementation; no performance rule frozen

**Date:** 2026-08-19

## Decision

Replace pointer-following incremental best-response logic with a compiled
arithmetic dependency tape. The first implementation is a correctness reference
that compiles a root-chance extensive-form game and one fixed finite policy into
contiguous numeric and index arrays. It must be independent of river action
constants and match both the generic full evaluator and the existing specialized
river recertifier.

Do not optimize the current two-level river formulas further. Stabilize the
tape contract first, force best-response action flips and support changes, then
reuse the same compiler on the wider river tree. C++/SIMD work starts only after
the richer trace fixes the topology and dirty-cone workload.

## Tape layout

Runtime nodes are stored in topological order. Every dependency index is lower
than its consumer index. Node and edge fields occupy flat contiguous arrays;
runtime evaluation follows integer offsets and never stores Python state objects
or child pointers.

The reference operations are:

1. range input;
2. Float64 constant;
3. Float64 affine reduction;
4. Float64 product;
5. information-set argmax; and
6. selector-controlled continuation value.

The compiler builds a deal/outcome-major root-input plane, fixed-policy utility
outputs, and one perfect-recall best-response circuit per player. An information
set owns one global argmax over its counterfactual action aggregates. Each
concrete history then selects its history-specific continuation using that same
action. This prevents the common error of replacing an imperfect-information
best response with a per-history perfect-information maximum.

Reverse dependencies are stored in CSR form. A source-relative recertification
marks changed root inputs, reaches their consumers through the reverse tape, and
recomputes marked nodes in increasing topological order. The eventual optimized
kernel has two execution modes:

- sparse: compact and process only dirty node IDs; and
- dense: sweep level/arity buckets branchlessly when dirty density exceeds a
  measured crossover.

The Python reference may sort its compact dirty list. It must expose node,
edge, dirty-cone, selector-flip, and contiguous-byte counts so the C++ layout can
be checked against an identical topology.

## Range and support contract

The tape is compiled over a declared root-outcome universe. Source probabilities
may be zero for outcomes supplied by a structurally identical target game, which
allows removal and previously unseen support to be tested without mutating the
runtime topology. A recertification rejects unknown outcomes, negative or
nonfinite weights, non-normalized distributions, different player counts, and
known structural-digest mismatches.

This is not a nearest-range cache. Direct strategy identity still requires exact
provenance. The outcome universe is an immutable topology epoch; a genuinely new
outcome outside it requires a new epoch or separately charged extension.

## Numerical contract

All cached values, action aggregates, probability deltas, products, and maxima
use Float64. Affine reductions use a stable summation order. Float32 neural or
solver storage may be promoted at this boundary later, but the recertification
tape itself is not permitted to accumulate in Float32.

Every target is evaluated from immutable source values using an epoch-stamped
overlay. No target-to-target numerical chaining is exposed. Thus repeated
recertifications cannot accumulate drift. Any future chained online mode must
add compensated accumulators, an explicit error budget, and periodic full
rebasing before it can replace this control.

The differential gate is maximum absolute error `1e-10` across fixed utilities,
all best-response values, deviation gains, NashConv, and two-player
exploitability. Best-response action identity is required away from declared
ties. Near-tie action changes are permitted only when both actions are equal
within the numerical gate and the resulting values remain exact.

## Finite-policy acceptance

The evaluator reports literal target exploitability; it never subtracts or
silences finite-policy noise internally. Reuse authorization instead has two
separate parameterized budgets:

`target exploitability <= absolute quality budget`

and

`target exploitability - source exploitability <= transfer-damage budget`.

Both must pass, subject only to a declared numerical guard no larger than the
validated evaluation-error envelope. A source that already violates the
absolute budget is not made deployable by a permissive transfer budget.

The difference between target and source exploitability is an operational
paired effect, not a canonical mathematical decomposition: best-response maxima
can switch and the signed difference can be negative. In multiplayer, this
scalar contract must be replaced by per-player unilateral-deviation budgets and
separate coalition threat models.

No budget value is selected or frozen in this checkpoint.

## Correctness gates

Before wider actions or optimized kernels, require:

1. source and target results match the full evaluator within `1e-10`;
2. river results independently match the specialized incremental evaluator;
3. both sparse and dense execution modes return identical values and actions;
4. blocker reweights, removals, unseen-hand additions, and deliberately forced
   best-response action flips are covered;
5. repeated source-relative calls in different target orders are invariant;
6. every runtime dependency points backward in the topological tape; and
7. acceptance tests prove that absolute and transfer budgets cannot mask one
   another.

Performance is recorded only as a diagnostic. The current object-heavy full
traversal is not an adequate optimized baseline, and `0.0227 ms` was a prior TV-
bound observation rather than a fixed latency SLA.

## Dissent protocol

**Confidence:** high that the arithmetic-circuit formulation can reproduce a
perfect-recall fixed-policy best response; moderate that dirty propagation will
stay sparse on wider heads-up trees; low that an explicit root-outcome universe
is viable for six-player hold'em.

**Opposing evidence:** selector changes can dirty large ancestor cones, dense
Bayesian likelihood updates can touch every root outcome, and the compiler may
duplicate deal-major and node-major information to obtain locality. A flat tape
can therefore trade pointer latency for excessive memory or full-array work.

**Largest unknown:** the sparse/dense crossover after multiple bet sizes and
factorized action-conditioned ranges are introduced.

**Cheapest falsification:** compile the current sequential river without using
its action constants, force the known one-percent blocker response flip, and
require exact agreement in sparse, dense, source-first, and target-first call
orders. Failure blocks wider-tree and C++ work.
