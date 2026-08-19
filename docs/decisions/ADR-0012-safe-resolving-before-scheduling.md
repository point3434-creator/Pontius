# ADR-0012: Preserve counterfactual frontiers before scheduling search

**Status:** Accepted 2026-08-19.

## Decision

Reject independent Bayesian public-belief re-solving as the production
composition rule. Preserve it and its exact local-gated variant as negative
controls. Do not spend the next iteration on CFR tuning, deeper trees, neural
leaves, or a learned compute allocator for this resolver.

Implement the next control in two-player zero-sum Kuhn as an augmented safe
resolving game. At a public replacement boundary, the opponent must retain an
option whose payoff matches the blueprint counterfactual value for the relevant
private information state. The resolver may replace strategy only if the
augmented game respects those frontier alternatives. Exact full-game NashConv
remains a hidden evaluation target, never a construction input.

This follows the safety target in
[Burch, Johanson, and Bowling (2014)](https://webdocs.cs.ualberta.ca/~mbowling/papers/14aaai-cfrd.pdf)
and the repeated/nested replacement setting in
[Brown and Sandholm (2017)](https://papers.neurips.cc/paper/6671-safe-and-nested-subgame-solving-for-imperfect-information-games.pdf).

The two-player gadget is a correctness oracle, not the final six-player
algorithm. Multiplayer poker is general-sum and has no automatic transfer of
the two-player safety theorem; even the underlying multiplayer regret theory
has materially weaker guarantees, as discussed by
[Gibson (2013)](https://arxiv.org/abs/1305.0034). After reproducing the
two-player property, test explicit per-opponent frontier constraints or
conservative max-margin relaxations in three-player Kuhn and reject them if
unilateral deviation gain increases.

## Evidence

EXP-0010 composes a posterior-correct root policy at every public decision. In
Kuhn2 it improves only 21/72 cases and has mean NashConv improvement
`-3.03646e-3`; in Kuhn3 it improves 2/24 with mean `-9.00442e-4`. An optimistic
exact local-NashConv gate raises those counts only to 29/72 and 4/24, with
negative mean quality per millisecond in both games.

A coherent global anchored solve improves 68/72 paired Kuhn2 rows and all 24
Kuhn3 rows. More decisively, when depth three reaches every true Kuhn2 terminal,
prefix/global search improves all six audit cases while independent continual
replacement harms all six. The remaining gap is strategy consistency across
replacement frontiers, not value approximation.

## Opposing evidence

- Local gating materially reduces harm in some LCFR cases and could remain a
  useful secondary veto after a safe resolver exists.
- A global coherent solve is not available at hold'em scale; its strong result
  does not prescribe the runtime architecture.
- Safe subgame-solving guarantees are cleanest in two-player zero-sum games.
  Six-player no-limit hold'em may require a measured approximation rather than
  a theorem.
- Opponent counterfactual-value vectors add model targets, memory traffic, and
  inference latency that must eventually earn their cost.

## Consequences

Neural leaf work remains blocked on resolver composition. The eventual leaf
interface must likely predict ranges, per-player continuation values, and
uncertainty or bounds—not only a scalar expected payoff. The scheduler's future
benefit term must be computed after frontier feasibility; otherwise it ranks
unsafe candidates.

The global full-tree solve becomes the coherent optimization control. Prefix,
Bayesian continual, local-gated continual, and permanent no-op remain mandatory
baselines. All compute comparisons include any required gate evaluation.

## Cheapest falsifying experiment

For two-player Kuhn at terminal depth, compute exact blueprint opponent
counterfactual values, construct the terminate/follow resolving gadget, and
replace one public-root strategy. Verify that opponent counterfactual values do
not fall below the blueprint boundary and that full-game exploitability does
not increase beyond numerical tolerance. Then compose all public roots and
repeat across blueprint strengths and anchors.

## Kill criterion

Stop the safe-resolving implementation and audit the gadget if any exact
two-player terminal-depth replacement violates its declared counterfactual
value constraint by more than the measured augmented-game solution residual
plus `1e-10`, or worsens exploitability beyond the theorem's residual-adjusted
bound. Do not generalize to multiplayer until this control passes.
