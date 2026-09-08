# ADR-0254: Final-Latin posterior panel is fresh and balanced

- Status: accepted label-free result; fresh convex replication authorized
- Date: 2026-08-22
- Implements: ADR-0253
- Clean preregistration commit: `a881bd5f2a4978771a1bd9892c15f104bffbea18`
- Result: `experiments/results/h32-convex-replication-posterior-manifest-v1.json`
- Result SHA-256: `502dce7e14fe4996e01697a7aa8839853c599fe700338eb39cb4bd04e06a49ba`

## Result

Every clean-Git, source-parent, prior-panel, checkpoint, blueprint, balance,
observation, disjointness, complete-Latin-square, target-ID freshness, digest
freshness, uniqueness, posterior-change, acting-player, hand-axis, marginal-
replay, finite, wall-time, zero-label, and null-population gate passes. The
CPU-only invocation completed in `90.760 s` and produced no warm step, convex
candidate, quality evaluation, certificate, or strategy label.

The Latin-E/F panel contains 12 source-bettor combinations absent from both the
opened Latin-A/B panel and the held-out Latin-C/D panel. Every source appears
twice, every observed bettor appears twice, and every predeclared convex acting
player appears twice. Across all three panels, the 36 possible source-bettor
combinations now appear exactly once.

All 12 target IDs, belief digests, and descriptor digests are absent from clean
parent commit `7f0c2bb`. Every target differs from its source and preserves the
exact h32 hand axes.

## Belief nondegeneracy

Observed-bettor marginal total variation ranges from `0.580627` to `0.712305`.
The predeclared last-responder acting-player marginal shift is smaller but
strictly nonzero on every target, ranging from `0.043732` to `0.193912`.

This positional attenuation is useful context for later interpretation, but it
is not an opportunity prediction and did not select or order a target. The
acting-player rule remains purely structural: `(bettor - 1) mod 6`.

## Decision

Accept and seal the 12 fresh identities. Authorize a separately preregistered
fresh convex-retreat strategy replication.

Use Latin-E as the primary six-target replication: it contains one target per
source, observed bettor, and acting player. Keep Latin-F quality labels unopened
as a balanced confirmatory reserve. This split is fixed from the Latin design,
not chosen from belief TV or strategy opportunity.

Retain factor `0.5`, the widest last-responder one-seat axis, at most one exact
multi-cut round, exactly two all-seat oracles per target, separate `2e-11` cap
and `1e-9` epigraph allowances, independent retreat certification, the full
conservative 15-second schedule, immutable external blueprint, and no safety
composition. A target that does not close or certify inside the frozen method
must abstain; do not add a round or tune the factor.

## Claims boundary

This result establishes fresh balanced posterior identities only. It makes no
strategy-quality, convex-transfer, population, deployment, multi-seat,
composition, cross-street, or poker-strength claim.
