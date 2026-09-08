# ADR-0177: Preregister a fresh h32 regret-vertex opportunity audit

- Status: accepted preregistration
- Date: 2026-08-21
- Depends on: ADR-0148, ADR-0154, ADR-0175, ADR-0176
- Config: `experiments/configs/h32-fresh-regret-vertex-opportunity-v1.json`

## Question

ADR-0176 found nonzero admissible radii but microscopic certified value for the
soft one-step DCFR public-block direction. Is the soft policy movement the weak
link, or do the selected public nodes contain little usable local opportunity?

Compare the soft direction with a deterministic, more decisive direction made
from the same one-step counterfactual-regret signal. A regret-vertex win is
positive evidence that the soft generator leaves certifiable value on the
table. A non-win cannot prove opportunity exhaustion because the two-direction
library remains only a lower bound on attainable local value.

This is an off-clock identification audit, not a live scheduler or a strategy-
quality claim.

## Fresh panel

Use the full three-board by two-family panel with previously unlabeled seat-1
blocker shifts:

| Target | Selected seat-1 hand | Frozen target SHA-256 |
|---|---|---|
| panel 1 balanced | `3s Ks` | `574a600b803f7980b70c8c1b9334aba2def3fea283b4aa8536c7c3df03bd6d26` |
| panel 1 blocker-heavy | `3c Ad` | `17296f1cb926397d8374ea0fba0a4d49197b913f3005df851cfdea89590cb640` |
| panel 2 balanced | `7s Ad` | `862f5df07d822a36dd378a9ea537dea5c48e882157f7b8c14040e56400326a17` |
| panel 2 blocker-heavy | `6d Qh` | `b0ab91f3eeb388ae0e5854dd57c3dded75ae0a64cc4f6baa7def53950f981c26` |
| panel 3 balanced | `5c 9h` | `d8ad6fc5c9f4bd9e486fb12aa83f3e86b1eaace694a8e0f21e6951adc32c83f8` |
| panel 3 blocker-heavy | `5s 9c` | `647c67acf4ebe3e1dab908dc614c1f23ea3dc59a2ab608eaebcd9a4685b8ca39` |

The target rule is unchanged: maximum opponent-axis card overlap, then hand
strength, then smallest canonical hand; double only that hand's positive unary
likelihood. Source, target, descriptor, hand-axis, and checkpoint identities
are frozen before any target policy step or quality label.

## Paired block library

Run one resident DCFR step from the numerically identical warm blueprint and
construct the same six 32-hand public-node blocks as ADR-0173. At each block,
compare two direction families:

1. `soft_dcfr`: the generated current-strategy change on that block;
2. `regret_vertex`: for each hand/infoset in the same block, move to the first
   action with maximum recovered instantaneous regret.

At DCFR iteration one, positive and negative regret accumulators both receive
the exact factor `1/2`. Recover the causal instantaneous regret as twice the
post-discount regret minus warm mass times blueprint probability. The vertex
rule, block opportunity summaries, and action tie-break are computed before
any candidate certificate label.

The online-style local opportunity proxy records the sum of positive best-
action regret and action-regret span across the block, normalized by game
payoff span. It is a diagnostic feature, not a selection rule in this audit.

## Exact adaptive scale search

Use the inherited 34-point grid from scale 1 through `2^-33`. Every queried
scale is independently certified against the immutable blueprint.

Each direction changes exactly one acting seat at exactly one public node with
one shared scalar. Along that scalar:

- for another response seat, best-response value is a maximum of affine
  functions and profile utility is affine, so deviation gain is convex;
- for the changed seat, best-response value is independent of its candidate
  policy and profile utility is affine; and
- each cap, the NashConv objective, and their intersection therefore have a
  complete sublevel interval containing scale zero.

Consequently complete grid points form a suffix. Check scale 1 and the floor,
then use exact discrete bisection to find the first complete point. NashConv is
convex on the same one-dimensional scope, so its ordered safe-grid values are
unimodal; use exact adjacent-value binary search to find the minimum. Exhaustive
synthetic controls cover every possible 34-point boundary and optimum and
require at most 16 exact queries per direction.

This optimization is invalid for multi-actor unions or multiple changed public
nodes on one path. Those scopes are excluded rather than silently searched.

## Identification and measurements

For each of 36 blocks, report both directions' largest complete scale, best
complete scale, best positive certified value, certificate rate, binding
constraint, and descriptive one-certificate street ledger. The bounded local
oracle is the larger exact value of the two directions, with soft DCFR winning
ties. Report soft capture fraction and regret-vertex uplift.

The audit may state that soft DCFR is generator-poor within this frozen library
when the regret vertex exceeds it. It may not infer global opportunity
exhaustion when the vertex does not win. Correlate the causal regret proxy with
soft value, bounded-oracle value, and vertex uplift across the 36 paired blocks,
but treat all correlations as descriptive.

## Fifteen-second boundary

The full adaptive search is off-clock. For each best observed row, separately
record warm-step time plus construction, one exact certificate, and a one-
second emission reserve. This answers whether a later precommitted one-attempt
rule could fit; it does not make the observed scale available online.

The immutable blueprint is always emitted.

## Outcome-neutral gates

Require six targets, six warm steps, 36 coherent blocks, 72 paired directions,
six blueprint labels, clean committed execution, accepted parents, all frozen
identities, numerical warm identity, exact direction-family order, single-node
single-actor scope, search invariants, no more than 16 queries per direction or
1,152 total, immutable anchors, independent certificates, finite recovered
regrets, blueprint emission, finite accounting, 60-second per-step and per-
certificate ceilings, the 12 GB pool ceiling, 1 GB physical-free floor, and a
broad 2,400-second audit ceiling.

Do not gate on radius, best scale, completion, stop reason, value, direction
winner, uplift, captured fraction, proxy correlation, or descriptive 15-second
fit.

## Interpretation boundary

Six constructed targets and 36 blocks are not a population. The bounded oracle
is not a global oracle. No result authorizes deployment, reanchoring,
composition, or a strategy-quality claim. A positive alternative-direction
result justifies a fresh live-rule holdout; a null result calls for either a
broader offline direction oracle or explicit acceptance that local opportunity
remains unidentified.
