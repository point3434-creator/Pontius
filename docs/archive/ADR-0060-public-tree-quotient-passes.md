# ADR-0060: Exact public-tree quotient passes decisively

**Status:** Implemented; every frozen gate passed

**Date:** 2026-08-19

## Result and provenance

The ADR-0059 audit evaluated seven disjoint scaling games and twelve stress
games spanning balanced, polarized, blocker-heavy, and correlated ranges at
three, five, and seven hands per seat. It checked uniform, hashed-dense, and
hashed-pure policies in every game: 19 games and 57 exact profile evaluations.
No validation or test group was materialized.

The frozen configuration SHA-256 is
`9f9f7ce2becc3c801e85a8061ff576679d712396fb89b7ae936ed590a6e78515`.
The result is
`experiments/results/multiway-public-tree-quotient-audit-v1.json`, SHA-256
`d9cadc0f4989ca5e1a5bee4fe9f380a98fa9bc23c6a43b425d24b73ee00ea62e`.
It ran from clean commit
`810166ae74132c2934ebc1dab8fa86538c1ca6fd` in 47.574 seconds.

Before the run, 337 repository tests passed in 57.983 seconds. The first audit
invocation stopped on its first game before completing any benchmark: the
hashed-dense constructor supplied positive weights, ordinary evaluation
normalized them implicitly, and the tape correctly required explicit
probabilities. Commit `810166a` made that normalization literal and added a
tape-validation test. The frozen games, digest scores, policies, gates, and
timing procedure did not change.

## Exactness verdict

Every correctness gate passed:

- maximum error against ordinary traversal across utilities, every unilateral
  response value, deviation gains, and NashConv: `2.13163e-14`;
- maximum quotient-specific error: `1.68754e-14`;
- quotient best-response action mismatches: `0`;
- dependency-tape control action mismatches: `0`;
- information schema mismatches: `0`;
- deal-specific public topology mismatches: `0`; and
- numeric layout failures: `0`.

The pure-policy arm creates zero opponent reach and unreachable information
sets. Literal action identity there is important: the quotient reproduces the
ordinary evaluator's legal-order tie behavior rather than dropping unreachable
states or inventing a tolerance.

## Three-player engineering result

The public tree has 25 nodes: 12 strategic and 13 terminal. That count remains
constant while the dependency tape materializes 25 states per deal and then
compiles a much larger scalar arithmetic graph.

| Hands/seat | Deals | Ordinary ms | Tape hot ms | Quotient hot ms | vs tape | Persistent quotient/tape |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 1 | `1.5364` | `0.2396` | `0.2772` | `0.864x` | `3.325%` |
| 2 | 8 | `10.7558` | `1.8526` | `0.2895` | `6.40x` | `1.811%` |
| 3 | 27 | `35.0047` | `5.8383` | `0.3041` | `19.20x` | `1.682%` |
| 4 | 64 | `84.8672` | `14.5003` | `0.3414` | `42.47x` | `1.653%` |
| 5 | 125 | `197.7163` | `28.5657` | `0.3850` | `74.20x` | `1.644%` |
| 6 | 216 | `347.7488` | `53.1332` | `0.4572` | `116.21x` | `1.641%` |
| 7 | 343 | `593.5368` | `87.0190` | `0.5028` | `173.07x` | `1.639%` |

On the frozen largest row, quotient compilation is `56.03x` faster than tape
compilation and hot evaluation is `1180.46x` faster than ordinary traversal.
The tape contains 8,575 tree states, 93,384 numeric nodes, and 173,040
dependency edges. The quotient retains 25 public nodes and one 343-deal axis.

Persistent quotient tensors occupy 114,276 bytes versus 6,970,924 tape runtime
bytes. Adding the quotient's conservative 271,656-byte hot-scratch estimate
gives 385,932 numeric bytes, `5.54%` of the tape's persistent runtime arrays.
Persistent and scratch accounting remain separate because their lifetimes and
allocator behavior differ.

Across all 19 rows, quotient compilation beats tape compilation. Quotient hot
evaluation beats ordinary traversal in all 19 and tape evaluation in 18; the
sole loss is the frozen one-deal row, where NumPy dispatch costs `0.0376` ms.
Across the twelve blocker/correlation stress rows, hot speedup over the tape is
`7.24x` to `128.72x`. Pooled row medians total 7.626 ms for the quotient,
531.925 ms for the tape, and 3,443.605 ms for ordinary traversal. These sums are
a workload diagnostic, not a latency claim for one decision.

## What caused the win

This is not belief compression. It removes two exact sources of waste:

1. materializing the identical public betting tree once per joint deal; and
2. interpreting a generic scalar dependency graph when the same arithmetic can
   stream over a contiguous deal axis.

Terminal hand ranks are computed once per `(deal, player)` rather than once in
every terminal branch. Behavioral probabilities are gathered once by private
hand and public history. Utility and response passes then use vector Float64
operations over deals. The growing rows amortize a roughly fixed Python/NumPy
dispatch cost, explaining the near-flat `0.277` to `0.503` ms curve over one to
343 deals.

## Six-player boundary

A post-result revealed diagnostic, not a frozen gate, compiled disjoint games
from two through six players. Public-node counts were 9, 25, 65, 161, and 385;
terminal counts were 5, 13, 33, 81, and 193. At six players and three hands per
seat, 729 explicit deals required 6,782,944 persistent numeric bytes plus an
estimated 15,711,408 hot-scratch bytes. Exact full-profile evaluation, including
all six unilateral best responses, took 24.177 ms in Python.

This establishes both sides of the result. Public-tree quotienting is a strong
oracle primitive and likely a production layout. It does not cure exponential
joint support. A hypothetical dense six-player seven-hand Cartesian belief has
117,649 deals; the current terminal tensor alone would be approximately 1.09
GB. Real hold'em ranges are vastly wider.

The full-profile timing also includes all unilateral certification responses.
An online value contraction need not compute those responses on every decision;
future benchmarks must separate runtime value/action evaluation from offline
strategic certification.

## Decision

Adopt `PublicTreeTensorEvaluator` as the exact enumerated control for this
multiway river topology. Keep the generic dependency tape for arbitrary game
trees, incremental source-relative deltas, and cross-checking; do not route
deal-invariant dense multiway evaluation through it by default.

Advance to a separately frozen structured-belief screen. It must distinguish:

- exact public-tree quotient speed already earned here;
- exact factor-graph contraction that avoids constructing a dense joint belief;
  and
- approximate rank truncation that changes the belief or value operator.

Every approximate arm remains gated by root utilities, every player's response
value and literal action map, normalized strategic harm, memory, and time.
Probability reconstruction error or value-tensor MSE alone cannot pass it.

## Dissent protocol

**Confidence:** very high in exact three-player equivalence and the measured
Python result; high that the quotient is the correct data layout; low that these
ratios transfer unchanged to a native implementation where the scalar tape
would also be vectorized.

**Opposing evidence:** a native fused tape could close much of the interpreter
gap. The quotient still stores terminal values by joint deal, and its scratch
footprint is larger than its persistent footprint.

**Largest risk:** treating a spectacular constant-factor and layout win as an
answer to six-player combinatorics.

**Cheapest falsification:** on a wider topology or native kernel, compare equal
Float64 semantics. If the quotient loses after compilation amortization, retain
its exact representation only as a teacher. If a structured representation
changes a response action before materially reducing explicit-deal work, reject
that representation.
