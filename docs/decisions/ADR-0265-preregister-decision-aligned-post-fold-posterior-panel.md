# ADR-0265: Preregister decision-aligned post-fold posterior panel

- Status: accepted label-blind preregistration before any post-fold strategy label
- Date: 2026-08-22
- Follows: ADR-0264
- Config: `experiments/configs/h32-post-fold-posterior-manifest-v1.json`
- Config SHA-256: `5c167f4e0603058e91e457f8f1a61c53741b7b724c5b4d19ddabcff91b84e02e`
- Runner SHA-256: `d5682a9233fe1015123702454250eab1bfc2e892734de0cd1602fd43f0b1e720`
- Control SHA-256: `c542e6dce06365e2a0f6e84ac0a6899f71e84f2043920853900b31d01237b694`

## Question

Can the six ADR-0264 current-decision sources support a second, genuinely new
and nondegenerate posterior panel when the first observed responder folds
instead of calls, without opening any strategy label?

This stage freezes beliefs, public continuations, and behavioral-axis shapes
only. It runs no warm step, convex master, response oracle, certificate,
quality evaluation, or strategy label.

## Frozen differential

Reuse the six ADR-0262 sources, boards, source blueprints, bettor schedule, and
current-actor schedule in their existing order. Preserve every check before
the bettor and the bettor's bet. Change exactly one observed action: the first
responder `(b + 1) mod 6` folds rather than calls. The second responder
`(b + 2) mod 6` is current immediately after that observation, and three
opponents remain downstream.

No marginal TV, post-call value, cap slack, cut count, timing, family, board,
or position may select, omit, replace, or reorder a target. All six target IDs,
belief digests, and descriptor digests must be absent from clean parent commit
`c46a622267b0581e2b0c67685a149a84f7446267` and disjoint from ADR-0262's
post-call identities.

Construct each posterior by multiplying the immutable source blueprint's exact
likelihood for the frozen public observations in order. Preserve the h32 hand
axes and the source checkpoint and blueprint identities.

## Label-blind gates

For every target, compile the actual continuation and require:

- a legal public prefix ending at the declared current decision;
- root actions exactly fold/call;
- four remaining responders: the current actor and three downstream players;
- exactly one acting public node, 32 h32 information sets, and 64 behavioral
  variables;
- no root-to-terminal path visiting the same seat twice; and
- deal-invariant continuation topology.

Also require clean Git; exact pinned provenance; passed source, post-call
manifest, and post-call strategy parents; ADR-0264's post-fold authorization;
balanced source, bettor, observed-responder, and acting-player roles; unique
and fresh target identities; nonzero marginal shifts for the bettor, observed
responder, and actor; exact hand axes; marginal split error at most `1e-12`;
finite output; CPU wall time below 600 seconds; zero strategy labels; and a
null strategy-population claim.

## Decision rule

If every gate passes, seal the six post-fold identities but keep their strategy
labels closed. A pass does not authorize the one-round GPU shadow trial.

Before those labels open, inventory the already-opened retained convex contexts
and separately preregister an off-clock full-convergence constraint-generation
census. That retrospective census may compute optimization labels on contexts
whose strategy evidence is already open; it is not label-free and must not use
these post-fold identities. Report the distribution of rounds to exact
epigraph closure, unique new response facets, oracle work, incumbent certified
value, and verified master upper-minus-incumbent lower gap. The census decides
whether one-round closure is common enough to demote the direction-library
branch in the live one-seat scope.

If any manifest gate fails, reject this panel before any post-fold GPU strategy
work. Do not substitute a different observed action, source, bettor, or actor
after seeing the failure.

## Claims boundary

The source boards and blueprints are retained; freshness applies only to the
post-fold posterior identities. The fixed six-context panel is not IID. A
passing manifest says nothing about safe value, closure rounds, global one-seat
optimality under deadline, direction-library obsolescence, deployment,
composition, cross-street behavior, multiplayer global safety, exploitation,
or poker strength.

One-seat convex generation has a finite global certificate when run to closure
under its proved sequence-form scope. ADR-0264 instead bounded the live engine
to one cut round and certified only the emitted retreat's safety and value.
Those are distinct claims; this preregistration preserves that distinction.

## Decision

Commit the runner, config, control, this ADR, roadmap, and generated status from
one clean tree. Invoke the CPU-only manifest exactly once. If it passes, seal
the identities and proceed to the retained-context closure-census
preregistration, not to post-fold strategy evaluation.
