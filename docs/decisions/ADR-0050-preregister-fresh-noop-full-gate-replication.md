# ADR-0050: Preregister the fresh no-op/full computation-gate replication

**Status:** Accepted before constructing fresh contexts

**Date:** 2026-08-19

## Decision

Evaluate the fixed `river-noop-full-gate-v1` once on newly seeded,
group-separated development boards and ranges. Do not refit its feature,
threshold, arms, solver regime, or gates. Construct no validation or test
context.

The frozen rule is `experiments/rules/river-noop-full-gate-v1.json`, SHA-256
`27d1d9b942dfe4659eee97feaacdb9ab13636e7e6e1d2e4b6adf32dabc3d0671`.
The frozen experiment configuration is
`experiments/configs/river-noop-full-gate-replication-v1.json`, SHA-256
`89364fa70196e069d00404493bdbe8e61025e4fe2833c587e74c158222b6a079`. The result target is
`experiments/results/river-noop-full-gate-replication-v1.json`.

## Frozen rule

Before candidate solving, compute
`range_delta_changed_deal_fraction` from the source and target joint ranges.
Choose no-op when it is at most `0.14835164835164835`; otherwise construct the
full `b3r2` candidate. Equality is no-op. No target name, range-family name,
future NashConv, exact recertification result, solver probe, or candidate-policy
movement may enter the decision.

The rule is a no-op/full computation gate. It makes no claim that individual
bet or raise actions can be pruned safely.

## Fresh workload

Request 36 board groups with seed `20261219`, four private hands per player,
and all four range families. Materialize only groups assigned to development by
the existing group splitter. The run requires at least twenty development board
groups; fewer is a preregistered failure, not permission to change the seed or
group count.

Cross the same 3x2 searched action universe: bet fractions `{0.25, 0.5, 0.75}`
and raise-to fractions `{1.5, 2.0}`. Build the same three support-preserving
range targets per context. Require every newly generated board and full-range
digest to be absent from the frozen discovery source; overlapping textual group
indices are irrelevant because the seed and cards define identity.

No reserved split may be generated and discarded after labels are inspected.
The generator receives `development` as its only included split from the start.

## Solver and measurement contract

Build a quality-matched full-game DCFR blueprint at the first checkpoint in
`{512, 1024, 2048, 4096}` whose NashConv divided by the searched multi-size
game's payoff span is at most `1e-5`. Failure to reach that threshold is a gate
failure.

For both `b3r1` and `b3r2`, warm-start DCFR with pseudo-regret mass
`0.1 * searched-game payoff span` and run the integer number of selective-tree
iterations not exceeding the 32-full-tree-iteration state-visit budget. Compose
the reached policy with the exact blueprint at untouched information sets and
evaluate the complete full game exactly.

The fixed rule may deploy only no-op or `b3r2`. `b3r1` is generated solely to
retain the discovery screen's compact no-op/near-full/full oracle denominator.
It cannot alter the fixed rule.

Normalize every strategy-quality label by
`MultiSizeRiverHoldem.payoff_span`, not a narrow context feature. Record both
raw and normalized outcomes. Charge the fixed-full control its `b3r2` cold
candidate time. Charge the adaptive rule the complete boundary-feature time for
every target and `b3r2` cold candidate time only when the frozen rule searches.
Offline labels, `b3r1`, exact accept diagnostics, and fitting cost are not
runtime work.

## Frozen gates

The replication passes only if:

1. at least twenty development board groups are present, with no discovery
   board/range overlap and no reserved context materialized;
2. every source blueprint reaches normalized NashConv at most `1e-5`;
3. the fixed rule strictly beats always-`b3r2` in aggregate raw reduction;
4. it strictly beats always-`b3r2` in aggregate searched-game-normalized
   reduction;
5. raw uplift is positive in at least 60% of board groups;
6. it captures at least 15% of the compact no-op/`b3r1`/`b3r2` oracle's raw
   opportunity over fixed full search;
7. aggregate deterministic state visits do not exceed fixed full;
8. conservatively charged raw reduction per millisecond strictly exceeds fixed
   full;
9. maximum per-target NashConv harm does not exceed fixed full; and
10. no-op and full search each occur on at least 10% of targets.

All strict comparisons use tolerance `1e-12`. Gate failure cannot be rescued by
changing the threshold, equality direction, group minimum, normalization,
feature charge, oracle arms, or solver parameters.

## Outcome policy

Passing advances this rule as the transparent causal scheduler baseline for the
next reduced-multiplayer workload. It still does not authorize reserved split
access or native specialization on its own. A learned scheduler must beat this
fixed rule after paying inference cost.

Failure retains always-full `b3r2` on this workload and permanently rejects
threshold retuning on the fresh artifact. Exact accept/no-op remains a teacher
and post-solve verifier, not evidence that the causal rule transferred.

## Dissent protocol

**Confidence:** moderate that the simple threshold transfers; high that this
run will answer that question honestly.

**Opposing evidence:** the discovery group gate passed only 7/11, and changed-
deal fraction may identify quirks of the three synthetic target constructors.

**Largest unknown:** whether range-update density predicts the value of full
search across new boards, pot sizes, deal counts, and correlations.

**Cheapest falsification:** any aggregate normalized loss, fewer than 60%
positive groups, or worse maximum harm on these fresh development groups.
