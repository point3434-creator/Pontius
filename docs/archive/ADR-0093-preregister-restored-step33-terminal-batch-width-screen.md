# ADR-0093: Preregister restored step-33 terminal batch-width screen

**Status:** Accepted after h4 tracing development, before any restored h32
step-33 timing or state

**Date:** 2026-08-20

## Decision

Before extending the h32 DCFR ladder, screen one existing runtime parameter:
the maximum heterogeneous terminal feature width per CuPy batch.

The frozen configuration is
`experiments/configs/leaf-adjoint-batch-width-audit-v1.json`, SHA-256
`7f41dd243903baa135371e9762b51a02864a4d791a89f30d7c8aae8648c4358f`.
The additive tracer/runner is
`src/pontius/leaf_adjoint_batch_width_audit.py`, SHA-256
`d41fab3383dd4f9d0fb65bc8acf3b7cbdbf7a06e06004e8e734b26036c74696f`.
The result target is
`experiments/results/leaf-adjoint-batch-width-audit-v1.json`.

The immutable checkpoint source is ADR-0092's 43 MB artifact, SHA-256
`242de5f0a42693248f98cc8f127f4fc892606df58e94d28c107d542b1276736b`.

This is a parameter and phase-attribution screen, not native GPU fusion and not
a strategy-quality experiment.

## Why this precedes iterations 33-128

ADR-0092 establishes two facts simultaneously:

1. average strategy quality is still improving materially at iteration 32;
   and
2. terminal contraction consumes 99.8% of every 21-29 second training step.

The existing width 384 forces 435 sparse transforms per balanced step and 311
per blocker-heavy step. Each transform builds CPU features, copies them to the
GPU, runs two CSR-dense products, copies compatible records back, then folds on
the CPU.

A wider batch may reduce synchronization and call overhead without changing
the algebra. The screen costs approximately six minutes. If it finds even a
10% fixed win, collecting that before 64 additional iterations in each family
is cheaper than extending first. If it fails, its phase trace gives the
evidence needed to scope a transfer-resident implementation.

## Frozen source and workload

For balanced and blocker-heavy h32 cases:

1. rebuild the exact ADR-0092 board, range, topology, sparse incidence
   operators, automata, and GPU operators;
2. locate the iteration-32 checkpoint in the immutable source artifact;
3. validate its embedded state digest, final-state digest, iteration, current
   policy digest, and average-policy digest;
4. restore it into a pristine cold DCFR solver; and
5. run exactly one alternating step to iteration 33.

Restore validation independently checks topology, private axes, information
schema, variant, and all accumulator values. Any source mismatch stops before
timing.

Do not evaluate NashConv or use step-33 quality to select a width. Every arm
starts from the same literal iteration-32 state. Its only customers are exact
state agreement and runtime economics.

## Frozen width order

Run one unselected width-384 warmup per family, followed by the measured order:

`384, 768, 1536, 1536, 768, 384`.

The warmup exercises both incidence directions, all six traversers, memory
pools, and kernel loading. It is reported and charged to total wall/resource
ceilings but excluded from median selection.

The measured order is mirrored to reduce monotone thermal/allocation drift.
Every width has exactly two repetitions per family, for 12 measured rows.
Reuse one compiled bidirectional GPU operator within a family; its upload is a
one-time reported cost, not charged to each repeated step.

Do not release the memory pool between widths. The warmup gives the first
width-384 arm reusable baseline-sized blocks; the mirrored final width-384 arm
then observes any benefit from larger retained blocks. Medians span both ends.

## Frozen tracing semantics

Wrap, but do not modify, each frozen `CuPySparseIncidenceDirection`. For every
transform record:

- direction;
- source/query record counts;
- feature width;
- H-to-D and D-to-H numeric bytes;
- H-to-D wall time;
- CUDA-event time for the two sparse products;
- D-to-H wall time;
- complete operator wall time; and
- CuPy used/total pool bytes.

Aggregate per exact step:

- transform call count and solver-reported sparse batch count;
- terminal and full-step wall time;
- transfer, kernel, and return times;
- operator-unattributed time;
- terminal time outside the GPU operator; and
- nonterminal CFR time.

Require transform-call count to equal the solver's batch count on every row.
This prevents a partial trace from producing a persuasive but false phase
breakdown.

## Numerical reference

The first measured width-384 result in each family is the numerical reference.
For every arm compare the complete iteration-33:

- regret accumulator table;
- average-strategy accumulator table;
- current behavioral policy; and
- average behavioral policy.

Require maximum accumulator and action-probability error at most `1e-9`, plus
mean policy TV at most `1e-10`. These are Float64 numerical-equivalence gates,
not bit-identity gates: changing rank-piece grouping can change summation order
without changing the mathematical update.

Record output policy and accumulator digests, but do not require them to match.
The screen tests numerical state equivalence; the original iteration-32 source
remains the continuation authority.

## Frozen selection and economic gates

For each family and width, take the median of two full step walls. Select one
global fixed width by:

`argmin_width sum_family(median_step_ms)`, ties to smaller width.

Do not select independently by family and do not fit a rule from observed
features. The output is one declared runtime constant for the ladder extension.

Require the selected width to deliver:

- at least `1.10x` pooled full-step speedup over width 384; and
- at least `2.0x` batch-count reduction in both families.

Also require strictly decreasing batch count as width rises. A screen that
fails either economic gate rejects batch widening as the next optimization but
retains its phase attribution.

## Resource and execution gates

Require:

- exactly 12 measured rows and two repetitions per family/width;
- exact source-state identity;
- every restored source at iteration 32 and output at iteration 33;
- every full step at most 60 seconds;
- host numeric peak at most 8 GB;
- CuPy pool total at most 12 GB;
- finite states and timing outputs;
- trace/batch identity; and
- total pre-serialization wall time at most 900 seconds.

The wider ceilings are deliberate scratch allowances, not new production
budgets. The RTX 5080 has roughly 16 GB device memory and the development host
64 GB; a passing width must still leave material headroom.

## Pre-freeze engineering disclosure

The tracer and comparison path have only h4 evidence.

From an exact restored h4 state:

| Width | Full step ms | Transform calls | Regret error | Current-policy error |
|---:|---:|---:|---:|---:|
| 96 | 260.37 | 249 | 0.0 | 0.0 |
| 192 | 222.41 | 119 | 0.0 | 0.0 |

The doubled width was 1.17x faster and reduced calls 2.09x. Trace calls exactly
matched solver batches. This proves that the wrapper observes the complete
operator path and that width can matter on a small control. It does not predict
the h32 winner.

Four parser/selection/comparison tests pass. They pin the mirrored schedule,
source/code hashes, pooled median selector, smaller-width tie break, numerical
table/policy comparisons, runtime environment, and all gates.

No h32 step-33 policy, accumulator, timing, batch count at width 768/1536,
phase split, memory peak, or selected width has been observed.

## Interpretation branches

- Numerical disagreement rejects widening even if it is fast.
- Width 384 selected, or less than 1.10x pooled speedup, rejects widening and
  sends the measured phase split directly to transfer-resident design.
- Width 768/1536 passing with transfer/call overhead falling authorizes that
  fixed width for the 64/128 continuation.
- Kernel time remaining dominant after widening favors sparse-kernel/layout
  work; transfer/return time dominating favors resident buffers; host residual
  dominating favors on-device feature construction and query folding.
- A selected arm near the 12 GB pool ceiling is a laboratory win but a poor
  production default; record the tradeoff rather than hiding it in speedup.

## Successor order

1. Adopt the selected fixed width only if every exactness and economic gate
   passes.
2. Resume both original iteration-32 states and extend the average/current plus
   acceptance-gated incumbent trace to iterations 64 and 128.
3. Run the h32 ADR-0054-style acceptance reconnection using real checkpoints.
4. Use this screen's phase attribution and the longer curve's value-per-second
   evidence to scope transfer-resident/native fusion.

The short width screen does not replace or postpone that strategic order; it
reduces the bill paid to reach it.

## Limitations

- One board and two constructed range families remain the entire h32 sample.
- Two timing repetitions are sufficient for a 20-second deterministic kernel
  screen, not for subtle sub-percent benchmarking.
- Pool history is controlled by a mirrored schedule, not isolated processes.
- The selected width is specific to this RTX 5080/CuPy/CUDA environment.
- No strategy quality is measured, so a pass cannot claim a stronger policy.

## Dissent protocol

**Confidence:** very high in source/state comparison; high in trace coverage;
moderate that a wider batch clears 1.10x; low which of 768 or 1536 wins.

**Opposing evidence:** sparse-dense work and transfer bytes are nearly constant
with width, so fewer calls may only move synchronization overhead. Larger
batches also raise peak memory and may reduce library efficiency.

**Largest risk:** optimizing a parameter that saves only a few percent while
delaying the valuable ladder. The 900-second ceiling and 1.10x gate limit that
risk; a failure immediately returns the project to extension/resident design.

**Cheapest falsification:** the first measured width-768 balanced step. It
reveals batch reduction, numerical state error, phase movement, and a directional
speed signal, but the frozen mirrored schedule still runs to completion.
