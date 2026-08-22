# ADR-0220: The action-conditioned posterior panel is fresh, balanced, and nondegenerate

- Status: accepted label-free manifest result
- Date: 2026-08-21
- Implements: ADR-0219
- Clean preregistration commit: `a3ac07d`
- Result: `experiments/results/h32-action-conditioned-posterior-manifest-v1.json`
- Result SHA-256: `f74e495e9f27e3693bdb6f4b842f957765e43a03cefcd3e691b4b5ba6d694ea3`

## Formal result

Every frozen manifest gate passes. All six source beliefs and average-64
blueprints reproduce their ADR-0145 digests. The two Latin rounds produce 12
unique target beliefs: every source appears twice, every observed bettor
appears twice, and the complete prefixes contain 42 action likelihood rows.

Every target and descriptor digest is absent from the pre-manifest commit
`6d966cb`. Every target differs from its source, preserves all hand axes, has
positive observed-action mass, and produces a nonzero acting-seat marginal
shift. Exact meet-in-the-middle marginal replay stays inside `1e-12`. The run
completed in `89.158 s` and generated zero warm steps, certificates, quality
evaluations, or strategy labels.

## The belief regime is materially wider

The acting-seat marginal TV ranges from `0.566986` to `0.722760`. The maximum
seat marginal TV has the same range and is attained by the final observed
bettor in every target. These are large action-conditioned range movements,
not small synthetic likelihood tweaks around the source.

The panel therefore gives the opportunity-magnitude and selector-transfer
questions a genuinely different belief regime. The target choice remains
outcome-independent: posterior magnitude was measured only after the balanced
source/bettor mapping was frozen.

## Decision

Authorize preregistration of the widened, regret-vertex-only corpus against
these exact 12 target and descriptor digests. Preserve all targets; do not
remove a low- or high-TV row after seeing later strategy labels.

The widened trial must:

- perform one device-fold warm step from the immutable source blueprint;
- enumerate every coherent changed public-node block rather than one block per
  seat;
- build one regret-vertex direction per block;
- complete all label-independent affine features and clock-priced capacity
  rows before opening exact strategy labels;
- derive live K from the accepted ADR-0212 ledger, not from future labels;
- report every target separately before pooled capture;
- preserve immutable-blueprint fallback and the frozen one-second reserve; and
- use ADR-0179 numerical ceilings for reassociated GPU reductions.

The candidate schedule must be frozen from public structure and the observed
prefix. Tier A remains forbidden as an exclusion filter by ADR-0206. Tier B
may rank only candidates whose charged rows fit the measured K.

## Scope

The panel is exact under the source blueprint action-likelihood model. It does
not root the h32 tensor layout at the post-action continuation state. The next
result will therefore be evidence about action-conditioned **range transfer**
and widened opportunity localization in the complete river game, not a full
continual-resolving or deployed-subgame result.

No strategy has been populated. This result makes no strategy-quality,
opportunity-distribution, transfer, deployment, population, composition, or
hardware claim.
