# ADR-0038: Multi-size transfer passes; absolute branch work is next

**Status:** Accepted

**Date:** 2026-08-19

## Decision

Accept `MultiSizeRiverHoldem` and the unchanged generic dependency tape as the
exact branching-factor reference. Three opening bets and two raise-to sizes do
not destroy sparse invalidation: two-deal range changes still dirty less than a
quarter of the tape, while factorized likelihood updates remain decisively
dense.

Do not conclude that branching is cheap. The wide tape performs approximately
2.7 times as much absolute sparse work as the matched one-bet/one-raise tree
even though its dirty percentage is slightly lower. The next research gate must
measure the strategy-quality numerator supplied by the extra actions. Only then
should we optimize action-lane sharing or commit the 3x2 lattice to a C++ kernel.

## Frozen evidence

The multi-size contract, implementation, and preregistration were committed as
`2a84afe`, `cbc766b`, and `4866d56` before the result was generated. The frozen
configuration SHA-256 is
`0246924028a0ed572b0cd8dad94112e44f7ad8e4c8266af53ba5323b516bb52c`.

The 2,814,654-byte result artifact is
`experiments/results/river-multi-size-dependency-development-v1.json`, SHA-256
`8198e6b0f013b1d1fe92a2fa0fcbbf1119cc0e6a22ab360aeae23c6c55c89d08`.
Its embedded Git state is clean at
`4866d56e6feef7aec7930d7e8b28f1cca1acab97`.

The deterministic split materialized seven development board groups and 28
four-family contexts. Across both matched tree shapes and three finite DCFR
checkpoints, the artifact contains 168 source-policy tapes and 840 target
recertifications. It also contains 168 independent wide-game payoff audits
covering 68,514 deal-specific terminal histories. No validation or test context
was requested or materialized.

## Exactness and rules result

Every preregistered gate passes. The dependency-tape SHA exactly matches the
pre-widening hash. Worst absolute evaluation error is `1.42109e-14`, versus the
`1e-10` gate. The frozen run has zero literal best-response action mismatches
and zero action-value loss. Sparse, dense, and automatic selector maps are
identical, every dependency is topological, and source-relative replay has
exactly zero value and action drift.

All 68,514 audited terminal histories match the independent contribution-based
payoff calculation bit-for-bit. This covers every combination of three bets,
two raises, folds, calls, private deals, and showdown results. The result is not
conditional on the dependency evaluator agreeing with itself.

## Matched topology growth

| Mean source topology | Fixed 1x1 | Wide 3x2 | Matched ratio |
|---|---:|---:|---:|
| Compiled tree states | 187.71 | 680.46 | 3.625x |
| Numeric tape nodes | 524.46 | 1,516.94 | 2.896x |
| Dependency edges | 974.11 | 3,038.75 | 3.120x |
| Best-response selectors | 18.00 | 60.00 | 3.333x |
| Contiguous runtime bytes | 39,170.75 | 116,854.70 | 2.985x |

The tree-state ratio is exact: each deal expands from eight post-deal states to
29. Numeric-node ratios range from `2.771x` to `3.139x` across matched finite
policies, while runtime-byte ratios range from `2.902x` to `3.129x`. The growth
is structural and consistent, not driven by one range family.

## Sparse locality versus absolute work

| Update | Fixed dirty | Wide dirty | Fixed nodes | Wide nodes | Wide/fixed nodes |
|---|---:|---:|---:|---:|---:|
| Blocker reweight | 17.750% | 16.493% | 92.34 | 248.54 | 2.686x |
| Unseen support | 15.715% | 14.833% | 81.73 | 223.43 | 2.734x |
| Factorized likelihood | 81.241% | 80.314% | 423.10 | 1,211.46 | 2.864x |

Sparse percentages improve slightly because the added action branches include
nodes outside a given changed deal's dependency cone. That improvement is real
but insufficient: absolute sparse recomputation grows `2.724x` for blocker
updates and `2.777x` for support changes. Every individual blocker pair grows
between `2.517x` and `2.920x` in dirty nodes; every support pair grows between
`2.628x` and `2.880x`.

The maximum wide sparse dirty fraction is `22.390%`; the aggregate maximum over
both shapes is `23.202%`, far below the `35%` gate. The minimum wide
factorized-dense fraction is `73.020%`. Automatic routing therefore selects
sparse for every sparse record and dense for every dense record with a large
unobserved gap between regimes.

## Selector sensitivity

Branching multiplies strategy discontinuities faster than dirty percentages.
Mean selector flips rise from `0.399` to `1.583` for blocker updates, from
`1.042` to `3.935` for unseen-support changes, and from `0.619` to `2.238` for
factorized likelihood updates. More legal sizes create more locally unstable
argmax decisions even while dependency propagation stays sparse.

This reinforces ADR-0035's separation: dirty-cone size, selector instability,
and target policy quality are different scheduler signals.

## Consequences

1. Retain sparse and dense tape paths. Branching does not collapse them into
   one regime.
2. Measure absolute nodes and bytes, never only dirty percentages. Relative
   sparsity can improve while latency-relevant work nearly triples.
3. Treat the 3x2 tree as a reference action universe, not a chosen deployment
   abstraction. Its extra actions have not yet demonstrated enough root-strategy
   quality to justify their cost.
4. Build the next laboratory around one strong full-universe blueprint and
   nested action masks. Complete off-tree blueprint behavior must remain defined
   so every candidate can be evaluated by exact full-universe best responses.
5. Compare fixed, nested, and adaptive action sets at equal state visits and
   wall time. Primary targets are exact full-universe NashConv reduction and
   root-strategy harm per millisecond, not convergence inside each restricted
   game.
6. If added actions earn their cost, exploit their regular layout with
   branch-major action lanes, shared deal features, and SIMD. If they do not,
   prune the lattice before writing the optimized kernel.
7. Factorized range updates remain an orthogonal bottleneck. Compact likelihood
   parameters should eventually propagate through sufficient statistics rather
   than being expanded into every changed deal.

## No latency claim

The recorded 27.581-second wall time includes finite DCFR, two game shapes,
compilation, all three tape modes, generic and specialized exact controls,
repeated best responses, payoff audits, and JSON generation. It is not an
online benchmark. This decision advances exactness and work geometry only.

## Dissent protocol

**Confidence:** high that sparse invalidation survives this heads-up 3x2 tree;
moderate that action-lane sharing can reduce its 2.7x absolute work multiplier;
low that these exact sizes or this one-raise shape are useful in six-player play.

**Opposing evidence:** the full joint range is still explicitly enumerated,
there are no re-raises or side pots, and selector flips grow roughly fourfold
for support changes. Earlier streets and multiple opponents may connect far
larger portions of the best-response graph.

**Largest unknown:** how much exact full-universe strategy quality the added
sizes buy per additional node and millisecond.

**Cheapest falsification:** warm-start matched fixed and adaptive action masks
from one strong 3x2 blueprint, evaluate every output in the full 3x2 game, and
show that added sizes fail to improve exact NashConv reduction per charged work.
If so, prune the action lattice before kernel optimization.
