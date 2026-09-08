# ADR-0086: Leaf-adjoint dense-free h32 DCFR passes

**Status:** Frozen audit accepted; exact offline h32 checkpoint generation
authorized, strategy quality still unmeasured

**Date:** 2026-08-20

## Result

The ADR-0085 audit ran from clean commit
`842499bcfb184fb709a44a3185378b0b5a232c91` and completed in 191.665 seconds.
Every frozen gate passed.

The canonical result is
`experiments/results/leaf-adjoint-cfr-gpu-audit-v1.json`. Its SHA-256 is
`58455716893afcff2cc19eb5000f0bb74b90fa6b49564f08762b9c9db2b023ee`
and its size is 12,677,017 bytes. The larger artifact is intentional: it stores
all four wide current/average policy pairs, not only summary statistics.

This is the first artifact in the program that performs complete DCFR updates
and emits real six-seat h32 policies without a Cartesian joint-deal table. It
establishes a strategy-generation path at wide axes. It does not establish
that the two-iteration policies are strong.

## Exact small-axis trajectory

The external-axis solver reproduced two complete alternating dense DCFR steps
on all four warm-start geometries.

| Hands | Family | Max regret error | Max sum error | Max current error | Max average error |
|---:|---|---:|---:|---:|---:|
| 4 | balanced | `8.88e-16` | `2.22e-16` | `1.33e-15` | `2.78e-16` |
| 4 | blocker-heavy | `2.03e-15` | `1.67e-16` | `3.22e-15` | `3.33e-16` |
| 7 | balanced | `8.88e-16` | `3.33e-16` | `2.00e-15` | `4.44e-16` |
| 7 | blocker-heavy | `2.33e-15` | `3.89e-16` | `2.44e-15` | `6.11e-16` |

The global maxima are `2.33e-15`, `3.89e-16`, `3.22e-15`, and `6.11e-16`,
respectively. These are five orders of magnitude inside the frozen `1e-10`
gates. The result verifies regret updates, DCFR discount order, traverser
alternation, own-reach averaging, and current/average policy extraction—not
only one conditional-value formula.

The forced off-path control produced 31 zero-reach information rows. Every
leaf-adjoint regret delta was bitwise zero and every row matched the dense
action table exactly. ADR-0084's raw-`argmax` problem is absent because the
solver consumes action numerators and regret deltas directly.

## SVD elimination is the measured mechanism

On the same balanced h7 initial policy:

- exact rounded public-cache step: 11,444.23 ms;
- heterogeneous leaf-adjoint step: 630.57 ms; and
- rounded-to-leaf speedup: `18.149x`.

The rounded control's regret table matched the dense first update within
`5.47e-15`. The speed difference is therefore not a change in policy, tree,
belief, or update semantics. Removing 1,152 public-node SVDs caused it.

Leaf adjoints are not the universal small-axis winner. The dense h7 reference
took about 198-353 ms per step while leaf adjoints took about 600-638 ms; at h4
the dense reference was roughly an order of magnitude faster. Keep the dense
deal-axis solver as the small exact teacher. Leaf adjoints exist for the width
where the dense tensor ceases to exist.

## The sealed GPU mechanism transfers

The untouched blocker-heavy h32 row passes the charged speed boundary:

| Family | CPU target read | GPU target read | Upload | Raw speedup | Charged speedup |
|---|---:|---:|---:|---:|---:|
| balanced | 27,339.17 ms | 5,917.41 ms | 10.57 ms | `4.620x` | `4.612x` |
| blocker-heavy | 18,743.73 ms | 4,253.47 ms | 7.48 ms | `4.407x` | `4.399x` |

Both charged results clear the frozen `3x` gate. Operator upload is already
small relative to one target read, so excluding it would not change the
conclusion. Host-to-device and device-to-host transfer for every feature batch
remain inside each GPU marginal and are not hidden.

CPU/GPU agreement is substantially inside tolerance:

| Family | Reach | Numerator | Regret | Conditional |
|---|---:|---:|---:|---:|
| balanced | `6.31e-16` | `3.94e-15` | `1.50e-15` | `1.32e-12` |
| blocker-heavy | `2.16e-15` | `1.79e-14` | `5.16e-15` | `3.14e-12` |

Maximum action-child reach disagreement was `1.39e-17` on GPU and exactly
zero in the CPU controls. Different sparse reduction order is visible, but it
is not strategically material at this precision.

## Complete wide steps

Each wide step updates all six traversers over 192 strategic public nodes,
6,144 private-hand information sets, and 12,288 hand-action regret entries.

| Family | Step 1 | Step 2 | Terminal batches/step | Host peak | GPU pool peak |
|---|---:|---:|---:|---:|---:|
| balanced | 29,010.12 ms | 28,943.26 ms | 435 | 1.497 GB | 0.965 GB |
| blocker-heavy | 21,378.00 ms | 21,225.63 ms | 311 | 1.145 GB | 2.133 GB |

All four steps are well below the 60-second gate. The larger blocker-heavy
CuPy pool despite fewer batches is allocator/work-shape telemetry, not a host
memory reversal; it remains below the 4 GB ceiling.

Terminal contraction consumed 99.77-99.85% of complete wall time. Reverse
public propagation, probability compilation, own-reach averaging, regret
application, and DCFR discounting collectively cost only about 42-49 ms per
step. This localizes the next performance work unusually cleanly: further
public-tree or accumulator optimization cannot materially improve this Python
engine. The terminal incidence/feature path is the bill.

The engine performed 1,158 terminal contractions and 192 strategic reads per
step. Balanced axes required 435 packed sparse batches; blocker-heavy axes
required 311. This explains most of the validation family's lower latency and
shows that payoff-state rank and packing width, not the public node count,
control the wide bill.

## The checkpoints are real but shallow

Both current policies moved `0.3046875` mean TV from uniform after the first
step. After step two, current-policy TV was `0.45827` balanced and `0.45787`
blocker-heavy. Average-policy TV after step two was `0.15813` and `0.15987`.

The first average remains uniform because averaging occurs before each
traverser's first regret update. This matches the dense solver's update order.
By step two the average has moved and all policies remain finite,
nonnegative, and normalized.

The step-two current profiles are already sharp: 5,309/6,144 balanced and
5,337/6,144 blocker-heavy information sets are pure. Their mean entropies are
about 0.0675 and 0.0672. The step-two averages have no pure rows, mean entropy
about 0.54, and only eight distinct action distributions. Those facts are
consistent with a two-step DCFR trajectory; they are not evidence of strategic
quality.

An independent post-run verifier recomputed all eight embedded policy digests,
checked all 49,152 serialized policy rows, and found maximum normalization
error `2.22e-16` with no negative or nonfinite probability. It also reproduced
the frozen config and implementation hashes. This diagnostic validates
artifact serialization but is not a retroactive gate.

## Decision

1. Accept the leaf-adjoint formulation as an exact solver bridge.
2. Accept SciPy CSR plus CuPy as the current offline h32 checkpoint engine for
   the reduced one-bet river game.
3. Retain dense joint-deal CFR as the faster small-axis teacher.
4. Reject rounded and unrounded public-node TT composition as complete CFR
   step engines. They remain useful controls and may still serve other
   fixed-policy readers.
5. Do not call the h32 output a blueprint, equilibrium, safe policy, or online
   resolver. No policy-quality quantity was measured.
6. Build an exact dense-free unilateral best-response/value evaluator before
   spending a long run on deeper checkpoints.

## Why best response is next

The same target-omitted terminal contractions can evaluate a literal best
response. In the reverse public pass:

- sum children at opponent nodes, as now; and
- select the maximum child numerator independently for every target hand at
  traverser nodes, instead of folding by the traverser's current policy.

This dynamic program handles repeated actions by the same traverser without
enumerating policy combinations. Summing the root hand numerators gives the
best-response utility; folding the same leaves by the supplied target policy
gives profile utility. Their difference yields one unilateral improvement.
All six improvements form exact reduced-game NashConv telemetry, while still
carrying the multiplayer caveat that NashConv is not two-player exploitability
or coalition safety.

The evaluator must first reproduce dense literal profile utilities, best-
response utilities, action policies, and NashConv at h4/h7 for all six seats.
Tie handling must be deterministic and value-preserving; no unguarded action
certificate follows from Float64 `argmax`. Once that bridge passes, evaluate
the embedded h32 two-step policies. Only then choose the length of a
preregistered h32 checkpoint ladder.

A deeper ladder must also serialize restartable solver state—regrets,
strategy sums, iteration, and provenance—not only current/average policies.
ADR-0085's policy artifacts are sufficient for evaluation and warm starts but
cannot exactly resume the same DCFR trajectory.

## What remains expensive

Twenty-one to twenty-nine seconds per reduced-game iteration is an offline
research result, not a quality-per-millisecond runtime. A 512-step balanced run
would take roughly four hours if the bill stayed flat. Before native work, the
exact best-response curve should tell us whether those hours buy strategy.

If they do, the measured target is now clear: fuse feature construction,
resident device batches, and the two incidence multiplies so policies and
terminal state remain on GPU across traversers. The current wrapper pays Python
packing and host/device traffic on every batch. If deeper DCFR does not reduce
the measured unilateral gap, accelerating this formulation would optimize the
wrong solver.

## Limitations

- The wide CPU/GPU oracle crosschecks traverser zero at the cold uniform
  profile; complete wide CPU trajectories were intentionally not charged.
- Wide full-step correctness is triangulated by exact small trajectories,
  wide CPU/GPU target identity, invariants, and checkpoint validity. There is
  no h32 dense oracle.
- Numeric memory excludes Python-object and JSON encoder overhead.
- The tree is an equal-stack one-bet river abstraction with no side pots, not
  full six-max no-limit hold'em.
- Multiplayer unilateral NashConv, once added, will not certify resistance to
  cooperating opponents.

## Dissent protocol

**Confidence:** very high that the new solver implements the same DCFR update
as the dense reference; high that the h32 GPU numerics are sound; high that
terminal contraction is the dominant optimization target; very low in the
strategic quality of two cold iterations.

**Opposing evidence:** the only wide policies are shallow and already sharply
current-policy biased; average-policy structure is extremely coarse; and no
best-response or acceptance metric has improved yet.

**Largest risk:** allowing a major infrastructure pass to substitute for the
original objective. The project seeks decision quality per millisecond, not
dense-free policy files. The artifact becomes strategically meaningful only
if measured policy quality improves under a compute bill.

**Cheapest falsification:** exact dense-free NashConv of the saved h32
step-two averages. If it is nonfinite, inconsistent with small dense controls,
or no better than uniform in a stable unilateral metric, stop the checkpoint
ladder and inspect solver/game semantics before optimizing or training longer.
