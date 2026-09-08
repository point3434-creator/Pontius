# ADR-0077: Correct source axis order before representation run

**Status:** Accepted after a pre-rank provenance stop and before any
canonical-source root composition or representation result

**Date:** 2026-08-20

## Decision

Keep ADR-0076 and commit `aea8251` immutable. Its first execution stopped after
0.331 seconds with `source artifact hand axes do not reproduce`, before the
first terminal library, root composition, rank screen, cap, candidate read, or
timing result. No v1 result artifact was written.

Run the unchanged ADR-0076 workload and gates through an additive axis-order
adapter. The correction configuration is
`experiments/configs/real-policy-representation-audit-v2.json`; its SHA-256 is
`ed5fb58fb7c1f84fa173b494f853c91338ed913d22a085d9c887aadd1f6f3781`.
The corrected result target is
`experiments/results/real-policy-representation-audit-v2.json`.

The correction freezes and verifies:

- the canonical source artifact SHA-256;
- the complete ADR-0076 v1 config SHA-256;
- the complete ADR-0076 implementation SHA-256; and
- the additive correction implementation SHA-256.

No rank cap, tolerance, gate, candidate, checkpoint, timing repeat, evaluator,
reuse count, or accounting formula changes.

## Cause

ADR-0076 regenerated the source factor-belief axes and compared their generator
order directly with `hand_axes` in the canonical artifact. The source generator
had instead serialized `PublicTreeTensorEvaluator.hands_by_player`, which
stably sorts each seat's supported hands lexicographically.

The two objects contain the same hands and define the same joint distribution,
but axis order is part of a tensor representation's provenance. Rejecting the
mismatch before rank computation was correct.

## Correction

For every seat independently:

1. stably sort its exact hole-card tuples lexicographically;
2. construct the old-column index of every sorted hand; and
3. apply that same permutation to every mixture component's unary-weight row.

Seat order, mixture weights, hands, card compatibility, public tree, source
policies, and all probabilities remain unchanged. When a downstream seat-order
screen permutes whole seat axes, each within-seat axis is already canonical and
the adapter leaves its whole-seat order intact.

The adapter is additive and temporary around the immutable v1 run. The v1
constructor binding is restored in a `finally` block even if execution fails.

## Pre-freeze validation

The correction was checked before any representation run on all four source
geometries:

| Geometry | Axis identity | Game provenance identity | Compatible deals |
|---|---|---|---:|
| h4 balanced | exact | exact | 1,158 |
| h4 blocker-heavy | exact | exact | 588 |
| h7 balanced | exact | exact | 33,455 |
| h7 blocker-heavy | exact | exact | 17,538 |

A separate unit test keys both the original and reordered materializations by
actual private hands and verifies identical unnormalized probability mass. The
v1 config still parses under its original hashes.

## Evidence boundary

The failed v1 invocation revealed only an ordering mismatch. It did not reveal
real-policy ranks, seat-order winners, cap errors, frontier sizes, clean-read
costs, recomposition costs, flat-evaluator costs, certificates, or any gate
outcome. ADR-0076 therefore remains the frozen experimental contract; ADR-0077
is a provenance-preserving executable correction, not a retune.

If v2 fails after producing any representation result, no further workload or
gate correction is authorized under this preregistration.

## Dissent protocol

**Confidence:** high that the adapter is a pure tensor-axis permutation; high
that the source distribution is unchanged; high that v1 stopped before result
reveal.

**Opposing evidence:** none on distribution identity across the four frozen
geometries. The remaining risks belong to the already frozen ADR-0076
representation hypotheses.

**Largest risk:** accidentally sorting whole seats rather than hands within a
seat, or sorting a hand axis without carrying all unary columns. Both are
explicitly tested and provenance-checked.

**Cheapest falsification:** any corrected geometry disagrees with the source
artifact's hand axes, game provenance digest, or compatible-deal count.
