# ADR-0127: Preregister the h32 one-size versus two-size resident-cache preflight

## Status

Frozen after ADR-0126 and before any h32 two-size resident-cache byte, pool,
middle-rank, construction-time, or warm-step measurement.

## Context

ADR-0126 established exact two-size leaf adjoints at h4 and h7.  The extra bet
size nearly doubled public nodes, terminal groups, raw automata, resident half
vectors, and total middle rank, while maximum rank and the set of 378
transition topologies remained invariant.  The current cache nevertheless
stores amount-specific half vectors independently.

The one-size resident lineage already exposes a material boundary.  Its
largest complete six-seat h32 cache contains `4,232,121,372` persistent numeric
bytes.  The sustained audit reached a `9,416,577,536`-byte CuPy pool high-water
mark under the frozen 12 GB ceiling.  Blindly doubling the cache and trying a
step would turn an allocation accident into the decision rule ADR-0126 asked
this preflight to prevent.

The frozen configuration is
`experiments/configs/h32-multi-size-resident-cache-preflight-v1.json`, SHA-256
`d3a1c0af41334b48aa07dcb10f73b7671d7cf22f29f822f8333bca55b5795aae`.
The additive runner is
`src/pontius/h32_multi_size_resident_cache_preflight.py`, SHA-256
`1f66626378a3b233b1924141b88b159c8cdc9a55204f7a5b19a86f3101c93ec0`.
The contribution-aware resident CFR bridge is
`src/pontius/multi_size_resident_leaf_adjoint_cfr.py`, SHA-256
`52f291a8c5278d2c03c9f3f9e85f3a77b9b254abdbd4260de3a1ca4a1663fa32`.
The result target is
`experiments/results/h32-multi-size-resident-cache-preflight-v1.json`.

## Frozen workload

Reuse the exact fresh h32 resident workload:

- board `4h 6s Td Qh As`;
- six equal 30-chip stacks and a 12-chip pot;
- 32 hands per seat and three mixture components;
- balanced and blocker-heavy range families;
- local seat-five blocker and all-seat strength target shifts; and
- the existing split-three exact card topology, sparse incidence operators,
  CuPy/CUDA environment, and feature width 384.

For every one of the four target beliefs, compile complete resident belief plus
six target-seat automaton caches for the one-size `(3)` and two-size `(3, 6)`
trees.  Alternate cold arm order as:

`one/two, two/one, two/one, one/two`.

Release only unreferenced pool blocks between arms.  The shared sparse GPU
operators remain live and are not charged to either cache construction bill.
Target descriptors and belief digests must reproduce the frozen resident
parent exactly.

## Measurements

For each target and width report:

- belief, automaton, and combined persistent numeric bytes;
- per-seat and total middle-rank width plus maximum rank;
- half-vector preparation, upload, and complete cold construction time;
- CuPy used and total bytes before and after construction;
- headroom below the 12 GB pool cap;
- physical device free bytes; and
- two-size/one-size ratios for persistent bytes, automaton bytes, total middle
  rank, and cold construction.

Also report raw automaton bytes, public nodes, terminal groups, automaton count,
and distinct transition topologies.  These are representation and systems
measurements, not action-quality metrics.

## Frozen headroom rule

Reserve the largest observed resident-lineage difference between warm pool
high-water and persistent cache bytes:

`9,416,577,536 - 4,232,121,372 = 5,184,456,164 bytes`.

This deliberately conservative remainder covers every non-cache live
allocation, scratch buffer, and allocator block visible at the prior maximum;
it is not mislabeled as an exact analytic scratch tensor count.

The raw two-size cache is safe for one step only if all four targets, after
complete cold construction, satisfy both:

1. headroom below the 12 GB CuPy-pool ceiling is at least
   `5,184,456,164` bytes; and
2. physical device free memory is at least `5,184,456,164` bytes.

The condition is conjunctive across all targets.  It is not weakened to the
selected warm-step target after observing bytes.

## Conditional warm step

If and only if the headroom rule passes, rebuild the balanced/local-blocker
two-size cache and execute exactly one complete alternating resident DCFR step.
Warm-start every information set at the uniform policy with positive regret
mass equal to `0.1` times the two-size payoff span.  This supplies a stable,
fully supported systems customer without inventing a two-size blueprint.

Report the marginal wall bill, terminal bill, sparse batches, middle rank, and
pool high-water.  Compare wall time with the frozen matching one-size resident
step from ADR-0120.  Do not serialize or evaluate the resulting policy.

If any target lacks headroom, execute zero h32 two-size steps.  The mandatory
branch is then to build an affine/shared-topology resident cache rather than
tune allocation order.  That implementation may use small exact controls, but
any shared-cache h32 allocation or step requires a new additive freeze.

## Frozen gates

Before h32, a two-hand implementation control must compare the complete sized
resident DCFR step with the transferred contribution-aware leaf path within
`2e-12` for every regret and average accumulator.

The h32 preflight additionally requires:

- a clean Git state and exact SHA identity for every parent, configuration,
  implementation, and GPU requirement;
- four targets in frozen family/shift order with exact target identities;
- 385 versus 763 public nodes and 64 versus 127 terminal groups;
- 384 versus 762 seat/group automata;
- exactly 378 distinct transition topologies for both widths;
- identical one-size and two-size maximum middle rank in every target;
- every cold cache construction within 120 seconds and below 12 GB pool total;
- exact compliance with the conditional zero-or-one widened-step branch;
- any authorized widened step within 120 seconds and below 12 GB pool total;
- zero strategy-quality evaluations; and
- total wall time within 1,200 seconds.

Raw headroom safety is a decision outcome, not a pass gate.  A clean unsafe
measurement passes the preflight precisely when it stops before the step and
selects the shared-cache branch.

## Pre-freeze controls

The new sized resident traverser passed both split directions and a complete
h2 alternating DCFR step.  Maximum regret and strategy-sum disagreement were
within `2e-12`; all 385 terminal nodes were contracted for each traverser.  The
cache identity checks reject a missing seat or a library/cache mismatch.

No h32 two-size resident cache has been compiled.  No two-size h32 persistent
byte count, pool total, middle rank, construction time, step time, policy, or
quality value has been observed.

## Interpretation

- **Safe:** one systems-only widened step measures the raw marginal bill.  It
  does not authorize training or a second step.
- **Unsafe:** stop before arithmetic and build the affine/shared-topology cache.
- **Topology or rank mismatch:** return to the contribution-aware terminal
  mapping; do not interpret memory economics.
- **Mechanism failure:** reject all h32 conclusions even if byte ratios look
  plausible.

No branch claims that the second size improves strategy, deserves its cost, or
belongs in a production abstraction.

## Dissent

**Confidence:** high that raw persistent bytes remain near the h7 ratio; high
that topology count and maximum rank remain invariant; moderate that the raw
cache can compile below 12 GB; low that it leaves the conservative warm reserve.

**Opposing evidence:** the RTX 5080 has roughly 16 GB physical memory, so the
raw cache may execute one laboratory step despite failing the stricter 12 GB
concurrency boundary.  That is not sufficient evidence to call it safe.

**Largest unknown:** how much resident payload the affine amount basis can
remove without increasing per-term contraction work or destabilizing Float64
action tables.

**Cheapest falsification:** the cold two-size balanced cache.  It exposes the
largest known one-size geometry and can reject the step before any policy state
is advanced.
