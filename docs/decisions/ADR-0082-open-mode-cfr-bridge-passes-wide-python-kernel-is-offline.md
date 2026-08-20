# ADR-0082: Open-mode CFR bridge passes; wide Python kernel is offline-only

**Status:** Conditional primitive and quotient-CFR semantics accepted; current
wide NumPy implementation rejected as a production or full-iteration kernel

**Date:** 2026-08-20

## Result

The frozen ADR-0081 audit completed from commit `a2b46b4` in 71.222 seconds.
The canonical result is
`experiments/results/open-mode-factor-tt-audit-v1.json`. Its SHA-256 is
`6793219bf378903f4c6a1ac6511086c1b2f09529ba6d759a48786a3855146ae4`,
and its size is 836,301 bytes.

All 768 checkpoint-16 infoset rows, 8,448 hand/action entries, four small
geometries, one semantic zero-reach control, and two wide geometries reproduce.
Every frozen gate passes.

## The solver bridge is exact at laboratory scale

Across both four/seven-hand axes and both range families:

- maximum counterfactual-reach error: `6.11e-16`;
- maximum action-numerator error: `2.59e-14`;
- maximum positive-reach conditional-value error: `5.44e-13`;
- maximum regret-delta error: `2.31e-14`;
- production quotient-CFR applied-regret bridge error: `7.77e-16`; and
- selected-action mismatches: zero.

The action result is not resting on accidental exact ties. The smallest
positive-hand gap between the top two literal action numerators is
`1.249e-7`, while the worst numerator error is `2.59e-14`. The narrowest
observed decision therefore has roughly 4.8 million times more gap than
representation error.

The forced unreachable branch creates 31 zero-reach target infosets. Every one
selects the first legal action and applies exactly zero regret change. There are
zero semantic mismatches. This closes the off-path convention gap rather than
merely bounding it numerically.

Accept the open-mode numerator/reach identity, public counterfactual unary
factorization, child-action batching interface, and exact action semantics as
the bridge from factor-TT values to quotient CFR.

## Small-axis economics are coherent

The 768 open reads total 2.557 seconds. Per-infoset latency has:

- minimum 0.614 ms;
- median 2.248 ms;
- 75th percentile 4.190 ms;
- 95th percentile 7.287 ms; and
- maximum 70.332 ms.

Feature width remains predictive rather than decorative. The complete width
range is 6 to 708. Per-geometry open-read totals are about 170-212 ms at four
hands and 1.016-1.159 seconds at seven hands. Six player-value cache
compositions cost about 0.42-0.46 seconds at four hands and 3.34-3.44 seconds
at seven hands.

The dense literal layout remains the audit bottleneck at seven hands: 4.56
seconds for blocker-heavy and 8.51 seconds for balanced. That cost is oracle
only and disappears on the wide runtime path.

Public-child batching is retained for bounded rank slicing and one shared
denominator. The earlier engineering screen showed no reliable mature-rank
speed advantage over separate child calls. Target-seat grouping on one half is
retained as a real mechanism: it obtains three hand axes from the same record
contributions without three incidence passes.

## The 32-hand representation passes cleanly

The wide arm constructs no Cartesian payoff and no one-hot tensor-train export.
It consumes int32 automaton transitions directly. Against independent
meet-in-the-middle factor-belief marginals:

- partition relative error: exactly zero;
- maximum marginal error: `9.71e-17`;
- constant-payoff conditional error: `6.66e-16`;
- maximum six-seat zero-sum residual: `1.77e-13`; and
- every two-action output is finite and legal.

Memory remains below the frozen ceiling:

| 32-hand family | Sparse automata | Unallocated one-hot export | Half vectors | Peak | Dense ratio |
|---|---:|---:|---:|---:|---:|
| balanced | 0.523 MB | 62.369 MB | 217.513 MB | 747.253 MB | 8.70% |
| blocker-heavy | 0.410 MB | 38.001 MB | 146.982 MB | 656.389 MB | 7.64% |

The balanced middle ranks are 103-104 for left-target automata and 75 for
right-target automata. Blocker-heavy ranks are 75-80 and 58. This is a genuine
dense-free conditional representation, not a scalar-only extrapolation.

## The current wide implementation is not an online kernel

Six all-check conditional terminal values cost:

- 17.259 seconds on balanced axes; and
- 11.505 seconds on blocker-heavy axes.

The independent wide marginal oracle adds 3.86-4.40 seconds, but is not a
runtime charge. Even excluding it, seconds per six terminal values cannot be
multiplied across 192 strategic public nodes or thousands of CFR iterations.

The representation passes; the NumPy incidence implementation fails the
economic interpretation. Do not implement a naive full 32-hand CFR iteration
by looping this reader. Do not call the 71-second audit wall time evidence of
online readiness.

## Bottleneck and next decision

For a 3/3 split, every source assignment contributes to 64 used-card subsets
and every query assignment reads 64 signed subsets. With `K` belief components
and middle rank `r`, the present Python path performs work proportional to

`64 * K * r * (source_records + query_records)`.

At 32 hands there are about 25,000 compatible records per half. The current
implementation repeatedly calls `bincount` by feature and materializes chunked
gathers. The topology is fixed, so this is not fundamentally irregular tree
work. It is two fixed sparse-linear operators:

- source subset accumulation `A @ features`; and
- signed query reconstruction `Q @ incidence`.

Compile `A` and `Q` once in CSR/CSC or an equivalent contiguous segmented
layout, then measure sparse-dense matrix multiplication on CPU and, if the
transfer bill is honest, GPU. Fuse denominator columns with value features so
the certificate/reach pass is not repeated. Compare against the frozen NumPy
kernel at h7, h16, and h32 with identical vectors and a hard memory bill.

Only after this incidence screen should a full dense-free quotient-CFR step be
built. The step remains the next semantic milestone, but multiplying a known
11-17 second primitive first would measure an avoidable implementation tax.

## Decision

1. Accept exact open-mode hand reaches, numerators, conditional values, and
   public-child action comparison.
2. Accept exact quotient-CFR regret and zero-reach action semantics.
3. Accept the direct sparse showdown-transition path as the wide terminal
   representation.
4. Reject the current wide NumPy reader as a production kernel; it is an exact
   teacher and structural oracle.
5. Retain child batching for memory/shared reach, without claiming a speed win.
6. Build and preregister the fixed sparse-incidence operator screen before a
   full 32-hand CFR iteration.

## Limitations

- Checkpoint-16 policies are real finite DCFR averages but carry no multiplayer
  convergence guarantee.
- Action identity is empirical over the frozen source workload, not a formal
  guarantee under arbitrary near-ties or approximate neural values.
- The wide arm evaluates structured terminals, not policy-conditioned values
  at all public nodes.
- Peak accounting covers numeric arrays, not Python object or allocator
  overhead.
- Nothing in this audit improves policy quality; it removes the conditional
  evaluation blocker needed to train and test a wider policy source.

## Dissent protocol

**Confidence:** very high in the conditional algebra and small-axis solver
bridge; high in wide memory correctness; low that generic library sparse
matrix multiplication alone reaches the eventual sub-millisecond target.

**Opposing evidence:** the 64-subset transform has high arithmetic intensity
but poor gather/scatter locality, GPU sparse operators can underutilize hardware,
and public-policy composition may remain more expensive than conditional
contraction even after this kernel improves.

**Largest risk:** optimizing the exact teacher deeply while the eventual best
quality/ms architecture needs a neural approximation for most leaves. The
screen must therefore report attainable kernel economics quickly and reject
the path if speedup is modest.

**Cheapest falsification:** a compiled sparse operator that does not materially
beat the frozen NumPy kernel at h32, or whose memory exceeds the current 747 MB
peak, rejects generic SpMM and sends the next work to a custom segmented SIMD
kernel or a different factorization—not to parameter tuning.
