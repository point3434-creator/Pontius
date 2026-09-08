# ADR-0013: The safe gadget is an oracle, not a deployment rule

**Status:** Accepted 2026-08-19.

## Decision

Accept the exact two-player terminate/follow gadget and its additive
finite-residual certificate as the reference safety mechanism. Retain the
strict exact-frontier gate as a non-harming control. Reject unconditional
finite-iteration Resolve as a deployable resolver, and do not transfer the
two-player result to multiplayer.

Before introducing neural frontier values or a multiplayer relaxation, build
an exact small-game constrained or max-margin strategy oracle. It must reveal
how much safe improvement is achievable independent of CFR convergence. Then
compare CFR variants, stopping rules, and optional warm starts against that
frontier-quality oracle on quality per millisecond.

The construction follows
[Burch, Johanson, and Bowling (2014)](https://webdocs.cs.ualberta.ca/~mbowling/papers/14aaai-cfrd.pdf):
initial chance uses reach excluding the opponent; the opponent may terminate
for its blueprint counterfactual-best-response value or follow into the copied,
properly scaled subgame. Only the resolver player's component is deployed.
Nested replacement follows the setting studied by
[Brown and Sandholm (2017)](https://papers.neurips.cc/paper/6671-safe-and-nested-subgame-solving-for-imperfect-information-games.pdf).

## Evidence

EXP-0011 covers four blueprint strengths, LCFR and CFR+, and 30, 100, 300, and
1,000 search iterations. Across 128 independently resolved public boundaries,
the exact residual-adjusted bound has zero failures. It also has zero failures
for all 32 root-forward composed profiles.

Unconditional finite-residual composition improves only 9/32 profiles. Its
mean NashConv improvement is `-7.05082e-3`, its worst is `-4.24750e-2`, and its
aggregate improvement per decision millisecond is `-2.80398e-5`. Correct game
construction does not make an under-solved gadget safe without accounting for
its residual.

The strict gate accepts 18/128 searched public histories. It improves 9/32
profiles, ties no-op in the median and worst case, and has mean improvement
`+1.27000e-3`. Its aggregate improvement per millisecond is `+5.06482e-6`.
The coherent global control achieves `+2.07946e-5`, about four times the
aggregate rate, at roughly half the mean decision compute. The safe interface
is now correct, but not yet efficient.

## Opposing evidence

- Exact counterfactual best responses are cheap in Kuhn and infeasible in
  hold'em; the strict gate is a label-generating oracle, not runtime machinery.
- The matrix is small and deterministic. Zero certificate failures validate
  this implementation, not every future depth-limited or approximate gadget.
- Strict gating is conservative. It discards candidates that improve the full
  game while violating some frontier by a finite solver residual.
- The global control is not an online architecture and is unanchored here. It
  harms strong blueprints, so its mean advantage is driven by weak regimes.
- Plain Resolve targets feasibility/reconstruction, not maximum improvement.
  A margin-aware objective may change the quality-per-millisecond ranking.

## Consequences

The resolver contract now requires opponent counterfactual-value vectors and
their error or upper-bound semantics. A scalar expected leaf payoff cannot
certify safe replacement. Solver residual, frontier inference error, and
certificate latency must be charged separately.

No neural leaf scaling or learned compute scheduler is authorized by this
result. Their eventual labels should come from exact safe-feasibility and
margin oracles, not from raw local NashConv. Permanent no-op, naïve Bayesian
composition, strict frontier gating, and coherent global search remain controls.

## Cheapest falsifying experiment

Solve the same Kuhn2 frontier with an independent exact constrained method.
Compare every CFR candidate's frontier vector, one-sided residual, and full-game
bound with the exact feasible set. If the exact method disagrees by more than
`1e-10`, audit reach normalization, mixed-to-behavioral conversion, and
best-response grouping before interpreting solver convergence.

## Kill criterion

Stop extension work if any exact single or nested Kuhn2 replacement violates
its residual-adjusted exploitability bound by more than `1e-10`. Do not relax
the frontier for multiplayer merely to increase acceptance rate.
