# ADR-0230: Two continuation steps fit the conservative street ledger

- Status: accepted label-free engineering result
- Date: 2026-08-22
- Implements: ADR-0229
- Clean preregistration commit: `3ef084b`
- Result: `experiments/results/h32-continuation-depth-ledger-v1.json`
- Result SHA-256: `bf6ccd59c922e521bb02128aa0ba88ce281aacc2670a27c3cc76b7b236d7cc24`

## Formal result

Every provenance, parent, arm-count, counterbalanced-order, warm-start,
latest-step-recovery, block-partition, convex-scope, six-row charge,
affine-intercept, memory, finite, immutable-emission, and no-label gate passes.
The clean run completed in `321.191 s` from commit `3ef084b`.

The artifact contains 12 targets, 24 independent arms, 36 synchronized solver
steps, 744 complete Tier-B candidate rows, and 3,720 opponent-BR-conditioned
rows. It serializes zero affine values, quality rows, certificates, or new
strategy labels. Maximum affine-intercept error is zero.

## The second step fits everywhere

The hard ledger charges every warm step, all 31 candidate rows, a 1,250 ms
certificate reserve, and a 1,000 ms emission reserve. Two-step ledgers range
from `7,535.463 ms` to `13,244.376 ms`, with median `9,661.398 ms`. The worst
target therefore retains `1,755.624 ms` of headroom; the best retains
`7,464.537 ms`.

All 12 two-step targets pass the 15-second boundary. This uses a certificate
reserve more than three times ADR-0228's measured maximum winner-proof cost,
so the promotion does not depend on those unusually fast proof observations.

The second step itself costs `706.767 ms` to `1,605.364 ms`, with median
`1,031.037 ms`. Relative to the paired one-step arms, complete two-step hard
ledgers add `692.404 ms` to `1,599.375 ms`. The added cost is almost entirely
the second solver pass: the 31-row pricing-bill difference ranges only from
`-28.643 ms` to `48.381 ms`.

Counterbalancing does not reveal an obvious order pathology. Every even target
runs one then two, every odd target runs two then one, and both groups retain
positive two-step headroom. This is descriptive timing evidence, not a formal
thermal model.

GPU-pool allocation peaks at `8,173,944,320` bytes and physical-free memory
never falls below `7,185,891,328` bytes. No additional resident cache or
strategy population is required by the second step.

## Decision

Accept the label-free differential. Two continuation warm steps are safely
affordable for this exact h32 continuation workload under the conservative
street ledger. Authorize a fresh held-out action-conditioned posterior panel
that compares one-step and two-step delivered exact value.

The fresh experiment must not reuse the 12 opened target combinations. Select
new `(board, source range family, observed bettor)` combinations before any
new posterior or strategy value is computed. Preserve:

- independent one-step and two-step solvers from the same restricted blueprint;
- latest-step instantaneous regret-vertex directions in both arms;
- all 31 legal continuation blocks and the full-affine winner rule;
- one independent exact winner certificate per arm;
- the hard 15-second boundary, 1,250 ms proof-start reserve, one-second
  emission reserve, and immutable fallback; and
- outcome-neutral validity gates.

The primary comparison is exact delivered value per target and per hard-ledger
second. A second step earns promotion only if it creates additional certified
value rather than motion; deadline fit alone is no quality evidence.

No strategy is populated. This result makes no two-step strategy-quality,
deployment, continual-resolving, composition, population, or broad poker-
strength claim.
