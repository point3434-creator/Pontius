# ADR-0068: Fixed-policy root TT is exact but no global compressed cap passes

**Status:** Implemented; exact controls pass, compressed-arm hypothesis fails

**Date:** 2026-08-19

## Result and provenance

The ADR-0067 audit compiled complete fixed six-player public policies bottom-up
through the 385-node river tree. At every node, it multiplied the acting seat's
policy unary into one TT core, directly summed action children, and rounded by
Float64 QR/SVD. An independent dense recursive public-tree oracle supplied root
tensor and utility labels.

The frozen configuration SHA-256 is
`5a192cb6bb5594f91f95c38cb76e613585cabfd3460a29bb571918c47a5d9322`.
The result is
`experiments/results/public-policy-root-tt-audit-v1.json`, SHA-256
`62539561cd4057d6138cf982c9f719f060c197b0c4f9ee51716db44dccdc7343`.
It ran from clean commit
`a41f1e17c8ed7fe0028d60c195e68a1b70606cf0` in 41.723 seconds. All 373
tests passed in 60.324 seconds before the frozen run.

## Exact controls pass

The implementation is not the reason for rejection. Every exact gate passes:

- maximum numerically rounded terminal-operator error: `7.314e-10`;
- maximum tolerance-only dense-root tensor error: `3.296e-11`;
- maximum tolerance-only root utility error: `3.085e-13`;
- maximum four-hand public-tree quotient disagreement: `2.665e-15`; and
- all required hashed-pure zero-reach rows are present.

The terminal error is inside but relatively near its frozen `1e-9` ceiling.
All 64 terminal groups deduplicate to 34 operators for one target player.
Maximum terminal numerical rank is 6 at four hands and 10 at seven hands.
Terminal payoff rank is therefore not the dominant failure.

## Compressed arms fail

| Arm | Max middle rank | Max normalized utility error | Max root storage ratio | Frozen verdict |
|---|---:|---:|---:|---|
| rank 8 | 8 | `0.0104775` | `0.1953` | reject: utility |
| rank 16 | 16 | `0.00304670` | `0.6328` | reject: utility + storage |
| rank 32 | 32 | `0.000634182` | `1.1328` | reject: utility + storage |
| tolerance-only | 202 | `1.03e-14` | `2.1328` | exact control |

The frozen normalized utility threshold is `0.0001`. Rank 8 misses it by
`104.78x`, rank 16 by `30.47x`, and rank 32 by `6.34x`. Rank 32's worst
absolute utility error is `0.01903`; rank 8 reaches `0.31433`.

All capped arms easily beat the feature-work proxy for 64 independent rank-8
passes: their middle-rank ratios are `0.0156`, `0.0313`, and `0.0625` versus
the frozen `0.25` ceiling. The architecture reduces contraction work but loses
too much value and, above rank 8, fails small-axis storage economics.

## Where rank grows

Maximum tolerance-only root middle ranks by policy family are:

- uniform: 26;
- hashed-pure: 75; and
- hashed-dense: 202.

On seven-hand balanced axes, hashed-dense root ranks reach
`(1,7,49,201,49,7,1)`; the blocker-heavy maximum middle rank is 202. These are
near the full `7^3 = 343` middle unfolding, despite terminal ranks no larger
than ten. Hand-dependent public-policy composition, not showdown, creates the
rank.

The worst compressed utility cases are hashed-pure, even though hashed-dense
has larger exact rank. Pure hand gates create sharp, discontinuous partitions
whose discarded directions matter disproportionately under the exact range.
This is another direct demonstration that numerical rank or tensor error alone
does not predict root harm.

Uniform policies are much easier: their exact middle ranks top out at 26. A
single global representation must nevertheless cover dense and off-path pure
policies; dropping those cases after seeing the result is prohibited.

## Decision

Reject one fixed-cap, original-seat-order root TT as the general public-policy
value representation. Retain the exact TT algebra and tolerance-only arm as
laboratory oracles. Do not respond by simply raising the cap: exact middle rank
already reaches 202, and the rank-32 storage ratio exceeds one on the four-hand
axis.

Before retaining public history as an explicit state bond, run the cheapest
structural falsification: elimination order.

There are only ten distinct unordered 3-versus-3 seat partitions. The direct
card contraction requires a middle split but not the original seat order. For
the frozen exact dense root tensors:

1. transpose private-hand modes across every 3/3 partition;
2. measure exact middle unfolding ranks and singular tails;
3. optimize within-half order for the remaining TT bonds and total storage;
4. apply fixed rank caps after the order is selected without belief labels;
5. contract the reordered operator with equivalently reordered exact factors;
   and
6. judge the same utility damage and storage gates.

If no single order transfers across policy/family/target cases, retain public
history rather than eliminating it. The next representation would be a tree or
tensor network with an explicit public-state bond, contracted jointly with the
card-factor topology. That preserves sparse/pure policy structure which a
single dense root TT destroys.

Conditional action-value and best-response work remains blocked on selecting a
value representation. Implementing it on a rejected root cap would multiply a
known error source.

## Dissent protocol

**Confidence:** very high in the rejection under the frozen global-cap rule;
high that policy composition is the rank source; moderate that variable order
can help; low that one order will cover all policies.

**Opposing evidence:** the storage failure is driven by a tiny four-hand dense
control where metadata dominates. A hybrid dense/sparse/TT implementation could
still use rank 32 on wide, smooth policies. It would require an explicit
selector and verification gate, not post-hoc exemption.

**Largest risk:** spending time optimizing TT order when the public-state graph,
not seat order, determines the irreducible treewidth.

**Cheapest falsification:** no 3/3 seat partition materially reduces the worst
exact middle rank or lets one preregistered cap meet the existing root-utility
gate.
