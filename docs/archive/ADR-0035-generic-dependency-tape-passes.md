# ADR-0035: The generic dependency tape passes; widen the betting tree

**Status:** Accepted

**Date:** 2026-08-19

## Decision

Accept the generic flat dependency tape as the exact fixed-policy
recertification control for root-chance games. It matches independent generic
and river-specific evaluators, propagates real best-response selector changes,
supports unseen source-zero outcomes, and cleanly separates sparse from dense
updates on the frozen development workload.

Stop expanding the specialized river recertifier and do not optimize the
Python tape for latency. The next gate is structural: parameterize a wider river
betting tree with at least three initial bet sizes and two legal raise sizes,
then reuse this exact tape unchanged to measure topology growth and invalidation
cones. C++/SIMD work remains premature until that branching-factor workload is
fixed.

## Frozen evidence

The preregistered runner, tests, decision, and configuration were committed as
`ad6f0d3` before the result was generated. The configuration SHA-256 is
`b6c474d269fa86f0aa8512195ad9f842d9ed219ae1fe56c1f4504729de49ceb5`.

The 2,642,172-byte artifact is
`experiments/results/dependency-tape-differential-development-v1.json`, SHA-256
`91c007dcf91a4ba7fc3d72cb4603752ba0f59543d144251633c7c13f64404aa2`.
Its embedded Git state is clean at
`ad6f0d3ffd0a7525e15fd41a8c42083068c5fbaa`.

The deterministic split materialized seven development board groups, 56
four-family contexts across the no-raise and sequential-raise shapes, 168
finite DCFR source-policy tapes, and 840 target recertifications. No validation
or test context was requested or materialized.

## Exactness result

Every frozen gate passes. Worst absolute disagreement across utilities,
best-response values, deviation gains, NashConv, and exploitability is
`7.10543e-15`, versus the `1e-10` gate. There are zero source or target
best-response action mismatches across full, sparse, dense, and automatic
execution. Every dependency is topological. Replaying the first target after
intervening targets has exactly zero value error and identical complete selector
maps, supporting the source-relative Float64 overlay contract.

This includes 529 observed selector changes relative to source: 138 under
sparse blocker reweights, 311 under unseen-hand support swaps, and 80 under
factorized-dense updates. Exact identity therefore did not pass merely because
all argmax choices stayed fixed.

## Invalidation geometry

The automatic `0.35` dirty-fraction threshold classified every record as
preregistered. The widest gap was stronger than required: the maximum dirty
fraction among sparse targets was `0.22523`, while the minimum among factorized-
dense targets was `0.61818`.

| Update family | Records | Mean changed deals | Mean dirty nodes | Mean sparse recomputation |
|---|---:|---:|---:|---:|
| Two-deal blocker reweight | 336 | 2.000 | 17.233% | 16.769% |
| Unseen-hand support swap | 336 | 2.000 | 15.374% | 14.910% |
| Factorized likelihood | 168 | 21.857 | 81.858% | 76.798% |

The two sparse families change a mean 9.121% of explicit deals. The factorized
update changes 99.286%. A dense execution sweep recomputes a mean 83.066% of all
numeric nodes because immutable input and constant nodes require no arithmetic.

The support swap is the notable result. Despite adding a previously absent
private hand and producing more than twice as many selector flips as the blocker
reweight, its dirty cone is slightly smaller. Selector instability and cone
size are related but not interchangeable; a scheduler should measure both.

## Tree-shape transfer

Adding the current fixed raise expands the mean compiled tree from 120 to 192
states, mean numeric nodes from 362.10 to 539.35, and mean flat runtime storage
from 26.61 to 40.24 KiB. Yet mean blocker dirty fraction changes only from
17.166% to 17.300%, and support dirty fraction only from 15.316% to 15.432%.

This is encouraging evidence that localized root changes do not automatically
consume the whole dependency graph. It is not yet a branching-factor result:
the extra tree has one fixed raise and a final binary response, not competing
bet sizes, re-raises, or earlier streets.

## Consequences

1. Keep exact provenance as the only direct strategy-cache identity. The tape
   certifies a fixed policy under a target range; it does not make nearby-range
   strategy reuse intrinsically safe.
2. Preserve both execution paths. Explicit sparse deltas benefit from dirty
   compaction, while compactly represented Bayesian updates may still require a
   dense arithmetic sweep.
3. Attack dense belief updates upstream. Passing a factorized likelihood through
   an expanded per-deal vector discards its algebraic advantage. The wider-tree
   experiment should record an explicit dense control, but the later optimized
   design should seek marginal, low-rank, or sufficient-statistic propagation.
4. Do not learn the sparse/dense classifier from this run. The two perturbation
   regimes are separated by a large empty middle; the observed `0.35` threshold
   is a valid control, not an optimized crossover.
5. Keep target quality and range-transfer damage as separate policy-layer
   budgets. No acceptance value is selected by this experiment.

## No performance claim

The artifact's 9.338-second wall time combines DCFR, tape compilation, repeated
generic and specialized controls, all three tape modes, best-response action
reconstruction, and JSON creation. It says nothing useful about online latency
or quality per millisecond. Only topology, work counts, exactness, and routing
decisions advance.

## Dissent protocol

**Confidence:** high in the exact generic tape contract; moderate that sparse
cones survive a multi-size heads-up river; low that explicit outcome-universe
enumeration transfers to six-player play.

**Opposing evidence:** the largest current tape has only 625 numeric nodes and
45,213 bytes. Factorized updates already dirty most of it. Wider legal actions
can multiply selector dependencies, and a six-player joint deal universe is not
memory-feasible as a direct Cartesian table.

**Largest unknown:** whether multiple action sizes cause localized deal changes
to reach most selector aggregates even when the root delta itself is sparse.

**Cheapest falsification:** compile the same ranges with three root bet sizes
and two raise sizes, require unchanged exactness, and measure the maximum sparse
dirty fraction. If sparse updates become near-dense, use the tape as a dense
control and redirect optimization toward factored ranges and shared subgraphs.
