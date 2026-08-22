# ADR-0275: Preregister post-fold failure closure-depth diagnostic

- Status: accepted retrospective preregistration before any additional post-fold optimizer label
- Date: 2026-08-22
- Follows: ADR-0274
- Config: `experiments/configs/h32-post-fold-failure-closure-diagnostic-v1.json`
- Config SHA-256: `75f0214592fef716851c64c37f48cf6afb0a6a2f06a96543297a230b88eae534`
- Runner SHA-256: `0aa13e7ae891b98e182a1aa9c04f792d26715141df48c11081bf5c80893d976f`
- Control SHA-256: `d250dd64778d5bd4736225cb821fd1ec6c9a003e915561682e7ad6c6822e55e4`

## Question

Are ADR-0274's two fresh one-round closure failures exactly round-two cases,
and what cut-extraction, master, and endpoint-oracle work would that additional
round require?

This is a conditional retrospective diagnostic. Targets are selected because
their fresh one-round endpoints failed; it estimates neither a population
closure rate nor unconditional runtime.

## Frozen targets

Use exactly these two failures in their original post-fold manifest order:

1. `panel_1/blocker_heavy/checks_then_bet_seat1_then_fold_seat2`
2. `panel_3/balanced/checks_then_bet_seat4_then_fold_seat5`

No passing post-fold target, retained post-call target, or wide-axis target may
join the diagnostic. The roster and order are outcome-selected but fixed before
opening any additional optimizer label.

## Inherited solver and setup

Invoke the byte-pinned ADR-0267 full-closure target implementation. Preserve
one warm DCFR step, source response rows, exact all-seat separation, multi-cut
row extraction, master, cap and epigraph allowances, `U - L` bound tolerance,
projection and KKT gates, 32-round cap, 240-second target cap, memory limits,
and immutable-blueprint emission.

Replace only the census setup through a scoped adapter to the already pinned
post-fold current-decision setup, then restore it on success or failure. Both
axes must remain one public node, 32 information sets, and 64 variables.

## Prefix reproduction

Before interpreting a later round, reproduce the fresh campaign's already-
opened prefix. For each target compare source NashConv, first and post-cut
master lower bounds, first and post-cut exact objectives, and the failed
post-cut gap within `2e-11`. Require exact first-cut player order and exact
post-cut violating-player order.

Policy digests remain diagnostic under ADR-0179; numerical and discrete
identity are authoritative. A reproduction failure rejects the diagnostic and
cannot be repaired by changing a tolerance or target.

## Closure depth and marginal work

Continue exact multi-cut generation until verified closure, the inherited
round/time cap, a no-new-facet stall, or a target error. Do not stop at a hoped-
for round two and do not add a new safety retreat.

For each additional round after the already-failed round-one endpoint, report:

- the violating players whose exact response rows are extracted;
- cut-extraction time;
- next master-solve time;
- next exact endpoint-oracle time; and
- their sum as marginal closure work.

This sum answers only the closure-path cost. A future live path would also
need to construct and independently certify a retreat from the newly closed
endpoint. The diagnostic therefore cannot itself admit a second round under
the street deadline.

## Target isolation and checkpoint

Attempt both targets in fixed order. Catch any target exception, discard its
incomplete candidate, clean the GPU pool, record the exact exception, atomically
checkpoint the complete outcome list, and continue. Every exception fails the
process gate; target isolation preserves evidence but does not bless an error.

Atomically replace a complete partial JSON after every target outcome. The
final result must prove two ordered attempts and one durable checkpoint per
outcome.

## Labels, gates, and decision

All added exact endpoint evaluations are explicitly retrospective optimizer
labels on already-opened targets. Generate zero new retreat labels, emit zero
candidates, and keep the population claim null.

Require clean Git before runtime initialization; byte-pinned passing parents;
the exact two-target inventory; setup restoration; two attempts; durable
checkpoints; zero target errors; prefix reproduction; all inherited identity,
row, master, projection, lower-bound, response-accounting, timing, memory, and
finite gates; explicit retrospective label counts; and immutable-blueprint
emission. Cap the two-target campaign at 600 seconds.

If both targets close at exactly round two, authorize only a separate deadline-
admission study. If either needs more depth, stalls, or is censored, keep global
closure off-clock. In neither branch does this diagnostic retire direction
generation or loosen the `13,967.616 ms` conservative floor.

## Decision

Commit the runner, config, controls, this ADR, roadmap, and generated status
from a clean tree. Invoke the diagnostic once. Do not pilot one failure, add a
retreat, change a tolerance, or use the first completed target to alter the
second.

## Claims boundary

The result will be conditional on two selected failures and cannot estimate
deployment rates. It adds no fresh context, strategy comparison, or safety
certificate. No live deadline admission, direction-obsolescence, multi-seat,
composition, cross-street, chip-EV, AIVAT, full-width, exploitation, or poker-
strength claim is authorized.
