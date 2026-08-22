# ADR-0229: Preregister the label-free continuation depth ledger

- Status: accepted label-free preregistration
- Date: 2026-08-22
- Follows: ADR-0228
- Experiment: `experiments/configs/h32-continuation-depth-ledger-v1.json`

## Context

ADR-0228 delivered exact safe one-step continuation value on all 12 targets
and left at least `4.436 s` inside the hard 15-second ledger. The next scarce
resource is search depth. Before spending fresh held-out labels, measure whether
a second complete continuation warm step and the same full 31-block proof bill
still fit.

The 12 contexts are already opened for strategy value. This experiment may use
them only as a retained timing and structural workload. It does not deserialize
ADR-0228's result and may not serialize any affine coefficient, envelope,
quality row, certificate, or new strategy label.

## Frozen paired differential

Run independent one-step and two-step arms for every target. Reset the solver,
resident context, and immutable restricted blueprint between arms. Counteract
simple thermal/order drift by running depths `(1, 2)` on even target indices
and `(2, 1)` on odd indices.

For each solver step, snapshot the regret table immediately before and after
the update. The solver discounts regrets at the end of each iteration. Invert
that sign-dependent DCFR discount exactly and subtract the pre-step table to
recover the latest step's instantaneous regret delta. Unit controls cover
positive, negative, and zero post-update rows. The candidate direction for
each arm is the pure regret vertex from that arm's latest recovered delta; the
two-step arm therefore measures what its second search step newly proposes,
not the accumulated warm-start prior.

Partition all 992 information sets into the exact 31 continuation public-node
blocks and consume them in public-tree preorder. For every block, build the
endpoint and price the acting seat's zero-contraction affine row plus exactly
five opponent-BR-conditioned rows. Record only structural digests, work,
memory, and synchronized timing.

## Frozen hard ledger

For each arm, charge:

- every measured warm-step wall time;
- all 31 measured complete Tier-B candidate rows;
- a conservative `1,250 ms` one-winner exact-certificate reserve; and
- the `1,000 ms` immutable-emission reserve.

The result is a development hard-ledger measurement, not a strategy-quality
label. The 1,250 ms certificate reserve exceeds ADR-0228's measured maximum
winner-proof cost but is frozen independently of any new two-step opportunity.

## Gates and decision

Require 12 targets, 24 arms, 36 solver steps, 744 candidate rows, 3,720
opponent rows, exact block partitions, counterbalanced order, warm-start
identity, zero own contractions, five opponent calls, latest-step recovery,
affine-intercept identity, safe memory, finite telemetry, immutable-blueprint
emission, and zero new labels. Timing and depth fit are outcomes, not validity
gates.

If every validity gate passes and every two-step hard ledger is at most
15,000 ms, authorize a fresh held-out action-conditioned posterior panel that
compares one-step and two-step exact delivered value under the same full-affine
winner rule. If any two-step target crosses the deadline, retain the proven
one-step path and do not open a two-step value trial. If a validity gate fails,
reject the differential.

No strategy is populated. This preregistration makes no two-step quality,
deployment, continual-resolving, composition, population, or broad poker-
strength claim.
