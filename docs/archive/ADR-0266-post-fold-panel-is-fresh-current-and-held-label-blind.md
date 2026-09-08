# ADR-0266: Post-fold panel is fresh, current, and held label-blind

- Status: accepted label-blind result; retrospective closure census authorized
- Date: 2026-08-22
- Implements: ADR-0265
- Clean preregistration commit: `649ffc713c61bec58c053c2d941a018e1ca50b19`
- Result: `experiments/results/h32-post-fold-posterior-manifest-v1.json`
- Result SHA-256: `01e424665ce7f7c81c6d15602eef716e18bb16c6a1035588831310ab90fcfc5f`

## Result

The single CPU-only invocation passes all 36 frozen provenance, parent,
authorization, checkpoint, blueprint, balance, observation, freshness,
uniqueness, disjointness, posterior, hand-axis, marginal-replay, legal-prefix,
current-player, root-action, downstream-geometry, behavioral-axis,
path-single-visit, topology, finite, wall-time, zero-label, and null-population
gates.

It completed in `60.207 s`, constructed six post-fold posterior identities and
six continuation topologies, and generated zero warm steps, convex candidates,
response oracles, certificates, quality evaluations, or strategy labels.

## Frozen action differential

Each prefix preserves the ADR-0262 checks and bet and changes only the first
observed response from call to fold. On every target:

- the declared acting player is the actual current fold/call player;
- four responders remain, including three downstream opponents;
- the continuation has 31 public nodes;
- the current player's complete axis has one public node, 32 h32 information
  sets, and 64 variables; and
- the path-single-visit and deal-invariant topology checks pass.

Source, bettor, observed responder, and current actor each occur exactly once.
Every target ID and digest is fresh at the clean preregistration base and every
post-fold belief is disjoint from the sealed post-call panel.

## Posterior nondegeneracy

The current actor's marginal total variation ranges from `0.037662` to
`0.130666`. The observed folder's shift ranges from `0.117232` to `0.286434`.
All source and target marginal split errors remain below the frozen `1e-12`
ceiling. These are belief and topology descriptors, not opportunity labels.

## Decision

Accept and seal the six post-fold identities. Keep every post-fold strategy
label closed.

Next, inventory the already-opened retained one-seat convex contexts and
preregister a retrospective off-clock constraint-generation census that runs
each eligible context to verified epigraph closure or a frozen resource cap.
The census may generate further optimization labels on already-opened contexts;
it is therefore not label-free. It must exclude these six post-fold identities.

The primary outputs are rounds to closure, unique new opponent-response facets,
exact oracle work and time, incumbent exact-certified value by round, verified
master upper bound, incumbent lower bound, and their gap. Only that
distribution may decide whether direction generation is operationally
dissolved under the live one-seat deadline. Until then, keep the existing ray
and vertex machinery as a cheap incumbent and fail-closed fallback.

## Claims boundary

The source boards and blueprints are retained and the six fixed contexts are
not IID. This result opens no strategy label and makes no safe-value,
rounds-to-closure, global-optimality-under-deadline, direction-obsolescence,
deployment, composition, cross-street, multiplayer-global-safety,
exploitation, or poker-strength claim.
