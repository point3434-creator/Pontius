# ADR-0029: Preregister blocker-sensitive range-reuse screen

**Status:** Accepted; frozen before the production development run

**Date:** 2026-08-19

## Decision

Measure exact strategy identity, topology reuse, range-conditioned policy warm
starts, and current-range recertification as separate operations. Approximate
range distance never creates a strategy-cache hit.

The frozen development configuration is
`experiments/configs/river-range-reuse-development-v1.json`, SHA-256
`68420e9adc608cbd56881d47397a0e65c8f17f935a8721a00f4d335d096e0135`.
Its deterministic split contains 19 development board groups, 76 four-family
source contexts, and 152 source/target pairs. No validation or test context is
requested or materialized.

## Cache boundary

Classify a lookup categorically:

1. `exact_strategy_hit`: structural and complete joint-range provenance
   digests are identical. A defensive cached-policy copy may be deployed.
2. `structural_only`: the public tree matches but joint-range provenance does
   not. Reuse only the information-set/action schema and a policy hint for
   numerical initialization. Direct strategy deployment is mechanically
   rejected.
3. `miss`: public structure differs. Reuse neither strategy nor schema.

Root joint total variation and conditional opponent-range distances are
diagnostics. No threshold on either changes this classification.

For a structurally identical two-player zero-sum game, one fixed cached policy
does admit a conservative quality certificate. A fixed profile value changes
by at most `payoff_span * TV`, and a best-response value changes by the same
amount. Therefore

`target exploitability <= source exploitability + 2 * payoff_span * TV`.

This bound may certify a stated exploitability ceiling without a target best-
response traversal. It does not make the ranges identical, certify policy
closeness, or extend to multiplayer. Every bound is checked against exact
target exploitability in this laboratory.

## Paired perturbations

For each source context, construct one player-0 and one player-1 conditional
shock. Within the rarest eligible private hand, choose a donor/recipient deal
pair with maximum showdown-outcome contrast. Move at most 1% root probability
and at most 75% of donor mass. Preserve joint support and the selected private-
hand marginal exactly. Record actual root TV, selected-hand conditional TV,
both deals, and provenance.

This is deliberately adversarial to a root-overlap heuristic: a small root
change can be a large posterior change at one private hand.

## Solver comparison

Use exact source equilibrium policies as a best-case cached hint and solve every
current target with DCFR. Compare cold initialization against five pseudo-
regret priors whose per-information-set mass is `payoff_span` times `0.01`,
`0.03`, `0.1`, `0.3`, or `1.0`. Checkpoints are 0, 1, 2, 3, 4, 6, 8, 12, and
16; checkpoint four is primary.

The structural cache supplies the already verified information-set/action
schema, so warm initialization must not traverse the game merely to rediscover
topology. Charge hash lookup, defensive hint copying, numerical initialization,
DCFR time, and one exact current-range recertification separately. Also report
cumulative repeated-recertification time. Source/target oracle construction is
a diagnostic teacher cost and is recorded separately; it is not hidden inside
online quality per millisecond.

At matched checkpoint and traversal work, select the minimum-exploitability
warm prior on four training folds and apply it to the fifth. The development
screen passes only if:

1. the selected warm arm strictly improves cold checkpoint-four
   exploitability in every board-group fold;
2. aggregate improvement removes at least 25% of cold residual exploitability
   above the exact target teacher;
3. one-shot charged reduction per millisecond improves in every fold; and
4. solver traversal state visits never exceed cold checkpoint four.

A passing screen authorizes freezing one warm-start rule before new reserved
data. It is not unseen transfer. A failure retains cold DCFR and does not permit
post-hoc threshold or prior changes to be called this experiment.

## Dissent protocol

**Confidence:** high that exact-hit and structural-only semantics are enforced;
moderate that a cached schema removes avoidable initialization traversal; low
that an exact-source policy is representative of finite production cache
entries.

**Opposing evidence:** exact source teachers are an optimistic hint, Python
timing can obscure sub-millisecond lookup costs, and exact current-range best
response is not scalable recertification.

**Largest unknown:** whether a 1% root shift creates enough conditional strategy
damage that warm-start bias costs more iterations than it saves.

**Cheapest falsification:** run the committed development configuration once
and compare every warm prior with cold DCFR under the frozen fold gates.
