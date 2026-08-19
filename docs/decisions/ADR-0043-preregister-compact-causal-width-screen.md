# ADR-0043: Preregister the compact causal width screen

**Status:** Accepted — evidence completed and rejected by ADR-0044

**Date:** 2026-08-19

## Decision

Freeze `experiments/rules/river-selective-width-screen-v1.json` before fitting
or cross-validating a selective-width rule. The screen may choose only no-op,
near-full `b3r1`, or full `b3r2` at the preregistered budget of 32
full-tree-equivalent iterations and warm mass `0.1 * payoff_span`.
The frozen rule-file SHA-256 is
`3a8c26ee23eefaeec87f42e23257d591734cd90abb997734e9a1761f7b385e93`.

This is a discovery screen on the already revealed ADR-0042 matrix. A pass may
freeze one fitted transparent tree for a fresh development replication. It does
not authorize validation, test, native specialization, neural fitting, or an
exact-label runtime gate.

## Why this is the next question

ADR-0042 establishes a `13.6057%` exact best-mask/no-op ceiling over
full-mask/no-op, but fixed pruning captures none of it. More importantly, the
raw shallow masks are often catastrophic. The unresolved bottleneck is no
longer whether action width matters; it is whether information available before
future full-game evaluation can safely choose search and width.

An exploratory arm-compression diagnostic found that no-op plus `{b3r1,
b3r2}` retains `85.03%` of the four-mask oracle opportunity. Because that
diagnostic was seen before this freeze, it may define the discovery candidate
set but is not evidence that the compact rule works. `b1r1` and `b2r1` remain
secondary oracle controls only.

## Frozen information boundary

The candidate family has three cumulative feature tiers:

1. five probability-delta geometry features;
2. those features plus five source/change range-context features; and
3. those ten plus six public blueprint behavior features.

The exact names are frozen in the machine-readable rule. Synthetic range-family
names, target names, source blueprint residuals, candidate solver probes,
candidate policy movement, NashConv, exploitability, best responses, future
reductions, winner identities, and oracle fields are not features.

Every adaptive candidate conservatively pays the entire recorded boundary
feature time for every target, even when it uses the smallest tier. This avoids
claiming a tier-level timing win before tier-isolated instrumentation exists.
The static full fallback pays no feature cost. A no-op decision pays features
but zero solver work. A searched arm pays its recorded cold exact-leaf solve
time and deterministic state visits. Offline fitting is not runtime work.

Exact candidate evaluation remains a label. A separately timed diagnostic may
show what an exact accept/reject stage could achieve, but it cannot affect the
causal screen verdict.

## Frozen transparent family

For each feature tier, maximum depth in `{1, 2}`, and uncertainty multiplier in
`{0, 1, 2}`, fit one deterministic numeric decision tree. This gives eighteen
adaptive specifications plus fixed full expansion.

At a leaf, compute each arm's payoff-normalized raw reduction separately within
each training board group. The leaf score is the mean of those group means
minus the frozen multiplier times their sample standard error. No-op wins a
tolerance tie, followed by full and then near-full search. A leaf must contain
at least twelve target instances and four distinct board groups.

Candidate thresholds are midpoints between distinct training values. Grow the
tree greedily, choosing the legal split with the largest risk-adjusted training
objective improvement. Stop when no split improves by more than `1e-12`, the
configured depth is reached, or the maximum leaf count is reached. Feature
name, threshold, and leaf identity break exact ties deterministically.

This is deliberately smaller than a neural model, boosted forest, or arbitrary
linear sweep. The artifact has only eleven independent groups, so greater model
capacity would manufacture precision.

## Grouped selection

Leave out one complete board group at a time. For every candidate
specification, fit only on the other ten groups and apply the resulting tree
once to the held-out group. Select the specification with maximum aggregate
held-out payoff-normalized raw reduction. Fixed full expansion wins a tolerance
tie; remaining ties prefer the cheaper feature tier, lower depth, lower risk
multiplier, and candidate identifier.

After selection, fit that one specification on all eleven discovery groups and
serialize the exact tree. Internal folds estimate the frozen fitting procedure;
they do not erase the fact that feature tiers were designed after ADR-0042.
Only a fresh replication can supply new evidence.

## Metrics and gates

The primary outcome is the causal rule's raw full-game NashConv reduction from
the stale blueprint. Exact no-op filtering is forbidden. Report both raw and
payoff-normalized totals.

The discovery screen passes only if the grouped out-of-fold rule:

1. strictly beats always-full `b3r2` in aggregate raw reduction;
2. strictly beats it in aggregate payoff-normalized reduction;
3. has positive raw uplift in at least 60% of board groups;
4. captures at least 15% of the compact exact oracle's raw opportunity over
   blind full search;
5. does not exceed full-search aggregate deterministic state visits;
6. strictly beats full search in raw reduction per conservatively charged
   serial Python millisecond; and
7. does not increase maximum per-target NashConv harm over blind full search.

The artifact must contain at least ten board groups and match the frozen source
and config hashes exactly.

Failure stops adaptive-width work on this exact workload. Passing authorizes
only committing the all-development fitted tree and preregistering a larger
fresh development replication before constructing it.

## Dissent protocol

**Confidence:** high that the procedure is causal and auditable; low to
moderate that eleven groups can select a transferable tree.

**Opposing evidence:** feature ranks are only moderate, full search is the best
fixed arm, public-policy features may cost more in a native implementation, and
the exact oracle's no-op accounts for much of the apparent headroom.

**Largest risk:** post-ADR-0042 feature design leaks development peculiarities
into the selected tree even though every internal evaluation is group-held-out.

**Cheapest falsification:** run this frozen screen once. If it passes, freeze
the serialized tree and evaluate it on newly generated development groups. If
it fails, do not rescue it with another feature, arm, depth, threshold, or risk
multiplier.
