# ADR-0234: Preregister held-out one-step versus two-step continuation value

- Status: accepted preregistration before any held-out strategy work
- Date: 2026-08-22
- Depends on: ADR-0230, ADR-0232, ADR-0233
- Config: `experiments/configs/h32-heldout-continuation-depth-value-v1.json`
- Config SHA-256: `d0569af7750eeb0246993f3abff980b80bb0137d375737fe5098b818ef6774bd`
- Implementation: `src/pontius/h32_heldout_continuation_depth_value_trial.py`
- Implementation SHA-256: `a3d8be9254963131677a745ac3a73efdd3aef9d2318e896b677c6f6d596f6d7e`
- Control test SHA-256: `5baf83fd3d670b10d6cd644528746422d8fd39d71084e15339c854b782bf531a`

## Question

On the sealed Latin-C/D panel, does a second continuation DCFR step buy
additional exact delivered value per charged wall-clock second, or only more
policy motion and elapsed time?

## Frozen experiment

Run independent one-step and two-step solvers from the same restricted
average-64 blueprint for each of the 12 ADR-0232 targets. Counterbalance arm
order by target index. Each arm uses the instantaneous regret delta from its
latest step, partitions every changed information set into all 31 legal
continuation public-node blocks, evaluates every block through the complete
six-seat affine envelope, and freezes the maximum positive complete winner
with structural tie-breaking.

All 24 feature matrices, schedules, winners, and scales must be complete before
any strategy teacher is queried. After that barrier, query one independent
incremental exact certificate for each frozen arm winner. The teacher cannot
change a direction, block, scale, winner, or arm. The actual emitted policy is
always the immutable restricted blueprint; the recorded selection is shadow
evidence only.

The live ledger starts immediately before the first solver step. It charges all
steps, all attempted block coefficients, the exact winner proof, and the fixed
1,000 ms emission reserve. A block may start only under the ADR-0228 guard using
the maximum complete candidate cost observed by ADR-0230 plus the 10 ms
envelope allowance and 1,250 ms proof reserve. A late or incomplete arm emits
the blueprint. Complete 31-block coverage is a validity gate, not an outcome.

## Payoff and plumbing correction

Acceptance guards and quality normalization use only the ADR-0233 shared
helpers and `layout.game.payoff_span`. The exact teacher is called directly;
the historical stack-based certificate wrapper is prohibited. Parent artifacts,
pass bits, environment metadata, result gates, and serialization use the shared
runner harness.

The solver and affine implementations are the byte-pinned ADR-0228/0230 device-
fold customers, not new fold primitives. Their current contraction buffers are
C-contiguous Float64 allocations and are not observed after folding. Any new
direct fold customer remains required to use the v2 successor from ADR-0233.

## Frozen comparison and decision

Report per-target and pooled delivered exact value, charged ledger time, and
value per charged ledger second. Promote two steps only if both conditions hold:

1. pooled two-step value exceeds pooled one-step value by more than one raw
   acceptance guard per target; and
2. pooled two-step value per charged ledger millisecond exceeds the one-step
   rate.

Otherwise retain one step. This rule is evaluated only after all outcome-
neutral provenance, identity, partition, affine, teacher, deadline, memory,
fallback, finite, and total-time gates pass.

## Claims boundary

This is a paired reduced-h32 depth comparison on 12 held-out posterior targets.
It is not evidence about more than two steps, other direction families, other
streets, deployment, composition, population performance, or broad poker
strength. No strategy-quality claim is made before the sealed result.

## Decision

Freeze this exact trial and run it once from a clean commit. If execution or
schema plumbing fails, reject the invocation without reading partial values and
preregister any correction separately.
