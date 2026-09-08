# ADR-0021: Exact range-sensitive river before scheduler fitting

**Status:** Accepted

**Date:** 2026-08-19

## Context

The Kuhn opportunity traces showed that adaptive allocation can beat a fixed
checkpoint, but their public states do not contain real card removal, nut
blockers, or high-dimensional ranges. Fitting a scheduler there would optimize
the wrong workload. Approximate cache reuse is especially dangerous: a small
amount of root probability can be the entire posterior at a rare private hand.

The next laboratory must retain exact teachers while introducing genuine poker
beliefs. It must also distinguish topology reuse from strategy reuse and prevent
future exact labels from entering online scheduling features.

## Decision

Build a heads-up, one-bet river microgame using the full 52-card deck, exact
best-five-of-seven showdown evaluation, configurable pot/stacks/bet size, and an
explicit normalized joint distribution over compatible private combinations.
Independent marginal ranges are only an input convenience: they are multiplied,
blocked deals are removed, and the resulting joint belief is renormalized.

The initial action tree is deliberately narrow: player 0 checks or makes one
fixed bet; player 1 folds or calls. This is enough to express value betting,
bluffing, bluff catching, card removal, and posterior range changes while a
normal-form LP remains an independent exact equilibrium teacher.

Cache identities are separated:

- The structural digest contains the board, pot, stacks, and bet size. It may
  identify reusable tree topology and board-dependent showdown work.
- The provenance digest additionally contains every joint deal probability.
  Only an identical provenance digest is a deployable exact strategy-cache hit.
- A structurally matching but range-different result may initialize a warm
  start or provide a speculative hint. It is not deployed until evaluated or
  recertified under the complete current joint range.

For structurally identical games, the value of one unchanged policy obeys

`|V_p(policy) - V_q(policy)| <= payoff_span * TV(p, q)`.

This is recorded as a diagnostic bound only. It does not certify equilibrium
policy reuse, best-response stability, or exploitability.

Generated contexts use four synthetic families: balanced strength coverage,
polarized aggressor ranges, deliberate cross-range blocker density, and
explicitly correlated joint beliefs. All family variants of one board share a
group ID and data split. A split filter prevents reserved boards from even
being solved while development data are produced.

Each CFR checkpoint records only causal inputs: exact supplied-range features,
solver work, regret state, policy movement, and measured solver cost. LP values,
best responses, exploitability, and future checkpoint outcomes are labels. A
perfect-information pooled-iteration allocator is reported as an optimistic
ceiling, never as a deployable scheduler.

## Exact checks

An adversarial pair assigns 99% probability to one identical deal and changes
only a 1% deal. Root joint total variation is `0.01`, but at the rare shared
player-1 hand the conditional opponent-range total variation is `1.0`. Against
the same always-bet policy, the exact best response at the same information-set
key flips from fold to call. Dynamic and exhaustive best responses agree.

The independent LP oracle recovers the analytical fixed-bet bluffing solution:
value hands bet with probability one, bluffs bet with probability `1/3`, and the
bluff catcher calls with probability `2/3`. Its value is `5/3` chips.

## Development pilot

The first developmental run contains 32 board groups, 128 range contexts, four
solver variants, and 6,656 checkpoint records. All 128 LP teachers have maximum
duality gap `1.24e-13` and maximum behavioral NashConv `1.28e-13`.

One iteration produces exactly no average-policy improvement because it only
records the initial uniform strategy. First improvement appears at checkpoint
two in 119/128 CFR, 112/128 LCFR, and 106/128 CFR+/DCFR contexts; the remainder
first improve at checkpoints three or four. Therefore a one-step myopic label
would again reject useful multi-step options.

At checkpoint 64, mean exploitability is `0.08251` for CFR, `0.01855` for LCFR,
`0.00757` for CFR+, and `0.00587` for DCFR. More work is not pointwise monotone:
42, 69, 65, and 70 of 128 runs respectively regress at least once between
recorded checkpoints, and 12-22 final policies are worse than an earlier
recorded policy.

At an average budget of two full iterations, a perfect pooled allocator improves
total quality over blindly deploying checkpoint two by 40.1% for CFR, 61.4% for
LCFR, 74.1% for CFR+, and 75.6% for DCFR. The advantage falls below 6% by an
average budget of four and below 2.3% by eight. This is real evidence for early
adaptive allocation, but the ceiling can move work between unrelated contexts
and sees future exploitability; it is not an online result.

The strongest early pilot signal is normalized positive regret mass. At
checkpoint two its Spearman correlation with normalized best future reduction
is `0.923`, `0.948`, `0.928`, and `0.963` for CFR, LCFR, CFR+, and DCFR. These are
unfitted development correlations on a synthetic microgame, not a frozen rule.

## Production development trace

The clean committed run contains 256 development board groups, 1,024 contexts,
4,096 solver trajectories, and 53,248 records. No validation or test context is
constructed. Provenance records clean commit `9e81d05`; the raw artifact SHA-256
is `f9c94e2fda06ac2c656acec74950a1afe5152e146923dcc2265e23b4f8ae6cb2`.
Maximum LP duality gap and behavioral NashConv are `1.09e-12`.

The pilot ordering replicates. At checkpoint 64, mean exploitability is
`0.07283` for CFR, `0.01697` for LCFR, `0.00834` for CFR+, and `0.00670` for
DCFR. Pointwise nonmonotonicity also replicates: 31.4%, 61.5%, 56.1%, and 63.1%
of the respective solver runs regress at least once. The final checkpoint is
worse than an earlier checkpoint in 10.5%-22.4% of runs.

On the fixed deterministic 128-context allocation sample, the perfect pooled
uplift at average budget two is 51.1%, 64.6%, 73.8%, and 75.9%. At budget four
the range is 8.15%-9.34%; at budget eight it is 2.19%-2.98%. The large earliest
ceiling is partly caused by iteration one's guaranteed zero average-policy
movement and must not be generalized to another solver output convention.

Checkpoint-two normalized accumulated positive regret retains Spearman
correlations `0.917`, `0.925`, `0.904`, and `0.943` with normalized best future
reduction. Five board-group-preserving fold correlations range from `0.886` to
`0.952`, so the association is not one small board subset.

There is, however, a structural confound. In this binary tree each player acts
at most once, so a freshly computed one-step positive counterfactual-regret
profile equals exact NashConv. The trace feature is different—it is the cheap,
variant-discounted accumulated CFR regret table—but this environment makes all
regret-based opportunity signals unusually favorable. Tests now enforce the
identity so it cannot be forgotten.

## Consequences

The production trace passes its replication gates but does not authorize a
learned scheduler. Fitting now would mostly learn the first-iteration artifact
and a shallow-tree regret identity. The next exact game adds a sequential river
raise response so at least one player acts twice; only transfer there can justify
freezing an opportunity rule. Reserved validation and test boards remain
unsolved.

Approximate cross-range strategy cache hits are rejected by construction. Later
cache work must separately measure exact provenance hits, structural-only reuse,
warm-start acceleration, and current-range recertification cost.

This checkpoint does not establish a six-player method. It is two-player
zero-sum, river-only, and uses one fixed bet. Multiplayer work must report
unilateral NashConv and explicit coalition/team best-response threat models;
"safe" remains reserved for guarantees that actually cover the stated threat
model.

## Subsequent decision

ADR-0022 records the exactly paired fixed-raise replication. It breaks the
local-regret identity, changes the primary label from total headroom to quality
per unit work, rejects static one-bet hardness transfer, and authorizes only one
paid-probe transparent scheduler screen.
