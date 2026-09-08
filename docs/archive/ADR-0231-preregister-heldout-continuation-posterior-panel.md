# ADR-0231: Preregister the held-out continuation posterior panel

- Status: accepted label-free preregistration
- Date: 2026-08-22
- Follows: ADR-0230
- Experiment: `experiments/configs/h32-heldout-continuation-posterior-manifest-v1.json`

## Decision

Freeze 12 unused `(board, source range family, observed bettor)` combinations
before any new posterior strategy value is computed. The opened panel used
Latin offsets zero and three across the six source contexts. The held-out panel
uses offsets one and four, producing two new targets per source and two per
bettor with no target-ID overlap.

Reconstruct each average-64 source blueprint and condition on every observed
check plus the final bet in public order. Record exact belief and descriptor
digests, marginal total variation, hand-axis identity, and contraction replay
error only. Require every digest to be unique, absent at clean base commit
`781a492`, different from its source, and causally nondegenerate.

This manifest performs zero warm steps, affine evaluations, quality queries,
certificates, or strategy labels. If all gates pass, authorize a separately
preregistered one-step versus two-step continuation value trial. If any target
is stale, overlapping, degenerate, or invalid, reject the panel before GPU
science.

The boards and source blueprints are retained; only the action-conditioned
board/family/bettor combinations are held out. No strategy is populated and no
quality, depth, deployment, population, or broad poker-strength claim is made.
