# ADR-0146: Preregister fresh-panel two-step target transfer

## Status

Frozen after ADR-0145 and before any fresh-panel target search step or target
quality measurement.

## Workload

Use the six exact source `average64` checkpoints and the twelve target beliefs
whose identities were fixed label-free in ADR-0142.  Each source receives its
local seat-3 blocker shift and all-seat strength shift.  The public game remains
the one-size `3`-chip tree.

Warm-start resident DCFR from the immutable source blueprint with regret mass
`0.1 * payoff_span`.  Run exactly two uninterrupted target steps.  The fixed
candidate portfolio is current 1, current 2, average 2, and behavioral
current-1/current-2 interpolation at `0.25`, `0.50`, and `0.75`.

Evaluate the blueprint and all six candidates completely for all six seats.
Select the minimum NashConv candidate inside the immutable blueprint's six
deviation-gain caps, with normalized guard `1e-10`; abstain to the blueprint
inside the guard band.  No selection outcome, improvement, or acceptance rate
is a gate.

## Certificate boundary

Each target certificate binds its source checkpoint, immutable `average64`
policy, target belief, blueprint deviation vector, cap vector, and guard.  It
expires after one public transition.  A selected candidate never becomes a new
anchor and no cumulative episode-safety claim is licensed.

## Gates and exclusions

Require exact source, target, warm-start, checkpoint, restore, interpolation,
finite, zero-sum, vector-accounting, cap, certificate, count, and resource
identities.  Run all twelve targets even if earlier outcomes are positive or
null.

Construct zero two-size trees and make no action-width claim.  A pass authorizes
reporting the one-size two-step transfer outcomes across this deterministic
panel; it does not establish board-population frequency, sequential safety, or
production readiness.
