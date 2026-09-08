# ADR-0253: Preregister final-Latin convex-replication posterior panel

- Status: accepted label-free preregistration before any Latin-E/F posterior or convex candidate
- Date: 2026-08-22
- Follows: ADR-0252
- Config: `experiments/configs/h32-convex-replication-posterior-manifest-v1.json`
- Config SHA-256: `55e0b761aeb72c75ed6b2ca00561b6feef2c51e98bcf6c1ee5f63e636ed13a39`
- Runner SHA-256: `0d1bc116083de86a8a2437bf9eaca3816233a6f432fbee02fac0db46f3e74f6b`
- Control SHA-256: `270cd5e51a10503e5402f766533738804f444cc61aa2b0f7b257acd2ea66081e`

## Question

Can the last 12 unused `(source board, range family, observed bettor)`
combinations be frozen as a balanced, causally nondegenerate, label-free panel
for the fresh convex-retreat replication authorized by ADR-0252?

This stage constructs beliefs and identities only. It runs no warm step,
convex master, candidate oracle, exact quality evaluation, certificate, or
strategy label.

## Frozen final Latin panel

The earlier opened panel used Latin offsets zero and three. The held-out depth
panel used offsets one and four. Freeze offsets two and five as Latin-E/F over
the same six source contexts. This produces two targets per source, two per
observed bettor, and no target-ID overlap with either prior panel.

Together, the three 12-target panels must cover all 36 source-bettor
combinations exactly once. Each new target ID and its computed belief and
descriptor digests must be absent from clean parent commit
`7f0c2bb6e694d71ee777055a38e5b27a181998db`.

Reuse the exact posterior construction: multiply every observed check and the
final bet likelihood from the immutable average-64 source blueprint in public
order. Preserve all h32 hand axes and require the posterior to differ from its
source.

## Frozen acting-player rule

For each observed bettor `b`, predeclare convex acting player `(b - 1) mod 6`.
This is the last responder in the no-raise post-bet continuation and therefore
has the widest path-single-visit axis: 16 public nodes and 512 h32 information
sets. The rule is position-equivariant, uses no opportunity or quality label,
never selects the observed bettor, and balances every acting player exactly
twice over the panel.

Record marginal total variation separately for the observed bettor and the
future convex acting player. Require both to be nonzero, but treat them only as
belief nondegeneracy descriptors, never as opportunity selectors.

## Gates

Require clean Git, all three pinned parents passed, all six source checkpoint
and blueprint identities, 12 unique targets, exact source/bettor/acting-player
balance, 42 observed action rows, disjointness from both prior panels, complete
36-combination coverage, fresh target IDs and digests, nonzero bettor and
acting-player shifts, exact hand-axis preservation, marginal split relative
error at most `1e-12`, finite output, total CPU wall time below 600 seconds,
zero new strategy labels, and null population claim.

If every gate passes, authorize only a separate preregistration for the fresh
convex-retreat strategy run. If any freshness, balance, identity, or
nondegeneracy gate fails, reject the panel before GPU work.

## Claims boundary

The boards and source blueprints are retained; freshness applies to the
action-conditioned source-bettor combinations and resulting posterior
identities. This manifest makes no strategy-quality, convex-transfer,
population, deployment, composition, cross-street, or poker-strength claim.

## Decision

Commit the runner, config, control, this ADR, roadmap, and generated status from
one clean tree. Invoke the CPU-only manifest exactly once, seal the identities,
and do not construct a convex candidate until the result is accepted.
