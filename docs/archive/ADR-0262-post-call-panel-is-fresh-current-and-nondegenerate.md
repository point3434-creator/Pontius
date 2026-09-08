# ADR-0262: Post-call panel is fresh, current, and nondegenerate

- Status: accepted label-blind result; decision-aligned live-shadow preregistration authorized
- Date: 2026-08-22
- Implements: ADR-0261
- Clean preregistration commit: `1cdbbcd40c4dc461ab4d7f18280a045fab89e9e1`
- Result: `experiments/results/h32-decision-aligned-posterior-manifest-v1.json`
- Result SHA-256: `738bc251a66289ae6623255ddba85cee0f1b695ec1b9163768db3b28d340ea98`

## Result

The single CPU-only invocation passes every frozen parent, authorization,
checkpoint, blueprint, balance, observation, freshness, uniqueness, posterior,
hand-axis, marginal-replay, legal-prefix, current-player, root-action,
downstream-geometry, behavioral-axis, path-single-visit, topology, finite,
wall-time, zero-label, and null-population gate.

It completed in `60.332 s`, constructed six post-call posterior identities and
six continuation topologies, and generated zero warm steps, convex candidates,
oracles, certificates, quality evaluations, or strategy labels.

## Deployment alignment

Every public prefix consists of the checks before one bettor, that bettor's
bet, and exactly the first responder's call. At the resulting continuation
root:

- the declared acting player is the actual current player;
- the legal actions are fold/call;
- four responders remain, so three opponents act downstream;
- the continuation has 31 public nodes;
- the current player's complete axis has one public node, 32 h32 information
  sets, and 64 variables; and
- the path-single-visit and deal-invariant topology checks pass.

This closes the scope mismatch in Latin-E/F without collapsing the problem to
the last responder's terminal choice.

## Posterior nondegeneracy

All six target IDs, belief digests, and descriptor digests are fresh at clean
parent commit `f7cce54`; all target beliefs differ from their source and remain
unique. The current acting player's marginal total variation ranges from
`0.062778` to `0.152469`. The directly observed caller's shift ranges from
`0.679209` to `0.841629`. Maximum source-or-target marginal split error is
`8.89e-14`, within the `1e-12` ceiling.

These are belief descriptors and topology facts, not opportunity labels.

## Decision

Accept and seal the six identities. Authorize a separate prospective
decision-aligned live-shadow strategy preregistration using all six targets in
manifest order, with no TV or Latin-label selection.

Preserve the existing one-round convex algorithm, factor-`0.5` retreat, exact
final certificate, `1.48e-9` interior requirement, complete measured and
conservative 15-second ledgers, campaign-wide candidate barrier, and immediate
immutable-blueprint fallback. Recompute the expected axis counts for the
one-node current-decision scope, but do not tune any numerical or quality
threshold from this label-free result.

## Claims boundary

The source boards and blueprints are retained and every observed response is a
call. The panel is fixed and position-balanced, not IID. This result makes no
strategy-quality, fallback-dominance, population, deployment, composition,
cross-street, global-optimality, or poker-strength claim.
