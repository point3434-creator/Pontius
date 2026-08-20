# ADR-0096: Corrected step-33 width screen rejects widening

**Status:** Accepted negative result; retain batch width 384, extend the
quality ladder before building a resident terminal kernel

**Date:** 2026-08-20

## Result

The frozen ADR-0095 successor completed from clean commit
`ad6a887` in 377.689 seconds. The canonical local artifact is
`experiments/results/leaf-adjoint-batch-width-audit-v2.json`:

- SHA-256:
  `5e34cb54f0be353320d1190ca0cce504fce327693f9d3de47d29a33350d471c5`;
- size: 47,875 bytes;
- config SHA-256:
  `f9b8a23221ce008d89013bcfad140567120ce841b6bf5a99cdb2bb608cbcc432`;
  and
- implementation SHA-256:
  `478143cb1d0b2a6144c9dcc76faf3e8d922e74825363fcb7698047b66ca35967`.

Sixteen of the eighteen component gates passed. The aggregate `passed` gate
is false because the two economic gates failed: no wider width achieved both
the required 1.10x pooled speedup and 2.0x batch-count reduction. The frozen
selector therefore retained width 384 with speedup `1.0x` and batch reduction
`1.0x`.

This is a scientific rejection of batch widening, not an execution rejection.
All 12 measured rows, both warmups, all summaries, and all correctness and
resource gates completed.

## Timing result

Each value below is the median of the mirrored two-repeat schedule.

### Balanced factor belief

| Width | Sparse calls | Call reduction | Step ms | Speedup vs 384 | GPU operator ms | Host terminal residual ms |
|---:|---:|---:|---:|---:|---:|---:|
| 384 | 435 | 1.000x | **28,321.1** | **1.000x** | 10,019.7 | 18,245.7 |
| 768 | 196 | 2.219x | 29,857.6 | 0.949x | 10,023.7 | 19,777.1 |
| 1536 | 87 | 5.000x | 32,504.4 | 0.871x | 10,006.0 | 22,437.1 |

### Blocker-heavy factor belief

| Width | Sparse calls | Call reduction | Step ms | Speedup vs 384 | GPU operator ms | Host terminal residual ms |
|---:|---:|---:|---:|---:|---:|---:|
| 384 | 311 | 1.000x | **21,202.5** | **1.000x** | 6,888.2 | 14,257.3 |
| 768 | 140 | 2.221x | 23,979.3 | 0.884x | 7,100.6 | 16,810.9 |
| 1536 | 68 | 4.574x | 24,720.9 | 0.858x | 6,999.9 | 17,651.3 |

Width 1536 makes a step 14.8% slower balanced and 16.6% slower
blocker-heavy despite removing 78-80% of transform calls. The mirrored order
also shows that this is not a simple first-arm warmup result: the final width
384 rows return to 28.35 and 21.38 seconds.

## Mechanistic attribution

Widening does not change the amount of numerical work crossing the device
boundary. Every balanced row transfers exactly 24.662 GB host-to-device and
24.714 GB device-to-host. Every blocker-heavy row transfers exactly 16.983 GB
and 17.002 GB. Median GPU operator wall time is also essentially invariant
within each family.

The entire regression appears in terminal work outside the traced GPU
operator:

- balanced host terminal residual grows from 18.246 to 22.437 seconds,
  an added 4.191 seconds;
- blocker-heavy grows from 14.257 to 17.651 seconds, an added 3.394 seconds;
  and
- the corresponding full-step regressions are 4.183 and 3.518 seconds.

At width 384, the GPU operator is only 35.4% of balanced step time and 32.5%
of blocker-heavy step time. The measured sparse kernel itself is 20.9% and
19.2%; host-to-device and device-to-host copies add roughly 14.3% and 13.2%.
The remaining 64-67% is CPU-side feature construction, concatenation, and
record folding around a fixed total feature width. Larger temporary matrices
make that work worse rather than amortizing it.

This localizes the next systems opportunity. A useful successor must change
the total residency and folding path: generate or retain features on device,
apply the sparse incidence operators there, reduce/fold there, and return only
per-hand leaf values or accumulator deltas. Merely issuing fewer, wider calls
cannot attack the dominant bill.

That is an architectural hypothesis, not a speedup claim. This screen does not
measure a resident implementation, and the theoretical removable fraction is
not an achievable bound once new kernel, storage, and synchronization costs
are charged.

## Numerical identity

All widened steps reproduce the width-384 reference well inside the frozen
gates:

- maximum regret-accumulator error: `1.27e-15`;
- maximum strategy-sum error: `0.0`;
- maximum current-policy probability error: `2.76e-14`;
- maximum current-policy mean total variation: `7.71e-17`;
- maximum average-policy probability error and mean total variation: `0.0`;
  and
- all source-state identities, output finiteness checks, and trace-call versus
  batch-count identities pass.

The parameter is therefore strategically interchangeable at this one-step
numerical tolerance. It is rejected solely because it buys less quality per
millisecond.

## Resource result

The maximum host numeric estimate is 1.965 GB. The CuPy pool reaches 11.928 GB
after the balanced width-1536 arms, just inside the frozen 12 GB gate. The pool
remains high when the mirrored schedule returns to narrower widths because
CuPy retains reusable blocks; the first balanced width-384 arm used only
0.965 GB.

This is another reason not to carry width 1536 into the ladder. It consumes
nearly the entire frozen pool allowance while making both families slower.

Maximum step time is 32.598 seconds and total audit time is 377.689 seconds,
inside the 60- and 900-second gates.

## Decision

1. Keep batch width 384 for the next h32 DCFR checkpoints.
2. Do not build a width selector. Both families choose the same incumbent and
   the losing mechanism is shared.
3. Do not infer that fewer Python/CuPy calls imply less total transfer or
   contraction work; report total bytes and host residual with call counts.
4. Continue the exact iteration-32 states to a staged 48/64 quality ladder,
   measuring current, average, and an exact-evaluated best-so-far incumbent.
5. Decide on a 128 extension from the frozen 64 evidence rather than paying the
   full continuation bill blindly.
6. Keep a transfer-resident terminal pipeline as the subsequent native target,
   but preregister it against this phase decomposition and full-step quality
   bill rather than optimizing isolated sparse kernels.

The order is intentional. Width tuning found no free speedup, but ADR-0092's
quality curve is still improving materially. The next highest-value experiment
is therefore more strategy under the known-good width, not a large kernel
rewrite before knowing how much additional strategy the current engine buys.

## What this establishes—and what it does not

This result establishes on one RTX 5080, one h32 board, one reduced betting
tree, and two constructed belief families that batch width is not the current
bottleneck. It provides unusually clean evidence because call count changes by
up to 5x while total bytes and operator time remain fixed.

It does not establish the performance of a custom CUDA kernel, CUDA graphs,
device-resident CFR state, other boards, different hand axes, larger public
trees, or full NLHE. It measures only restored iteration 33 and no new
NashConv point. The project remains a reduced-game laboratory, not a deployed
six-max bot.

## Dissent protocol

**Confidence:** very high in the rejection of widths 768 and 1536 for this
implementation and workload; high in the phase localization; moderate that a
resident pipeline is the best eventual native target.

**Opposing evidence:** only two repeats per width were used and GPU-pool
retention is schedule-dependent. Nevertheless, both mirrored families return
to the faster 384 regime, while the invariant byte and operator measurements
explain the direction.

**Largest risk:** host residual is a subtraction of traced bills, not a
fine-grained profiler attribution. It localizes the loss outside the operator
but does not yet separate feature creation, concatenation, Python allocation,
and folding.

**Cheapest falsification:** implement one device-resident micro-slice that
keeps a fixed terminal group through feature generation, sparse transforms,
and folding, then compare full output and end-to-end group wall time. Do not
generalize from an isolated CSR benchmark.
