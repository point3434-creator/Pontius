# ADR-0184: Ordinary deep DCFR plateaus while purification remains direction-sensitive

- Status: accepted corrected prospective result
- Date: 2026-08-21
- Implements: ADR-0181, ADR-0183
- Rejected source result: `experiments/results/h32-deep-horizon-opportunity-v1.json`
- Corrected replay: `experiments/results/h32-deep-horizon-correction-v1.json`
- Corrected replay SHA-256: `da2e385f9ed87921f4c9a0b74064ea31d401275bb591af6cae906b3fe499f7bf`

## Correction identity

The ADR-0183 read-only replay passed every gate. It verified that
`target_identity` was the only substantive false v1 gate, rehashed both stored
descriptors, matched both beliefs and descriptors to ADR-0178, reproduced every
other true gate, and copied the aggregate identically. It executed no GPU work,
solver step, policy construction, certificate, or strategy-quality evaluation.

The original artifact remains a rejected invocation under ADR-0182. This ADR
accepts only the metadata-corrected measurement.

## Ordinary depth result

All 128 resident steps and 981 exact certificate queries completed. Every one
of the 84 endpoint/block directions had a complete scale. Aggregate positive
certified value was:

| Endpoint | Certified value |
|---|---:|
| current 8 | `2.0332e-7` |
| average 8 | `2.0877e-7` |
| current 32 | `1.8840e-7` |
| average 32 | `2.1980e-7` |
| current 64 | `2.1492e-7` |
| average 64 | `2.6231e-7` |
| purified average 64 | `1.3093e-6` |

Average-64 was the best ordinary endpoint, but it was only `1.2564x` the best
step-8 endpoint. It therefore failed the frozen twofold-plus-one-guard-per-block
material-depth rule. Ordinary deep value was also only `2.9686%` of ADR-0178's
retained two-direction bounded oracle and `69.64%` of the retained one-step soft
value on the same twelve blocks.

Depth was not uniformly helpful. Balanced panel 1 average value rose `1.4778x`
from step 8 to 64, while blocker-heavy panel 3 rose only `1.0366x`. Current-32
fell below current-8 in aggregate. Ordinary DCFR therefore produces more policy
motion with depth without a commensurate increase in certifiable value.

The average policy's mean total variation from the blueprint grew about
`4.77x` on panel 1 and `4.65x` on panel 3 from step 8 to 64. That larger motion
bought only the value ratios above. Deep search is not promoted as the next
architecture.

## Purification result

Purified average-64 captured `4.9912x` the value of raw average-64 and `3.4759x`
the retained one-step soft value, but only `14.817%` of ADR-0178's bounded
oracle. The effect was sharply target- and seat-dependent:

- on balanced panel 1, purification captured only `0.6250x` raw average-64;
- on blocker-heavy panel 3, it captured `11.1735x` raw average-64; and
- `1.1926e-6`, or about 91.1% of all purified value, came from acting seat 0 on
  the blocker-heavy target at full scale.

Thus purification is positive evidence for direction sensitivity, not a
universal endpoint rule. It neither transfers across the two disclosed targets
nor catches the regret vertex, which remains the stronger bounded direction on
this panel.

## Systems result

The adaptive searches used 981 of the 1,344 allowed certificate queries, a
27.01% reduction from the full bound. Maximum resident step time was `8.475 s`;
maximum certificate time was `1.394 s`. Peak GPU-pool total was
`6,719,463,936` bytes and physical free memory never fell below
`8,540,651,520` bytes. The complete GPU run took `1691.32 s`.

These off-clock costs do not authorize any observed endpoint, scale, or
purification choice inside the 15-second street.

## Decision

Accept the corrected mechanism result and reject ordinary 32-64-step DCFR as
the next architecture on this panel. The frozen material-depth hypothesis did
not pass. Do not expand the deep ladder, promote purified-average-64, or infer
that the immutable envelope has exhausted all local opportunity.

The evidence now points to generator direction and opportunity identification:

1. regret vertices beat one-step soft movement by about `20.54x` in ADR-0178;
2. ordinary depth adds only `1.26x` over step 8 here; and
3. purification can add `4.99x` over raw deep average, but only on one target
   and still remains far below the regret vertex.

The next gate should be a separately preregistered causal direction/opportunity
screen on fresh contexts. Compare the failed regret-mass proxy with action-gap,
directional-slope, and one explicitly charged vertex-certificate probe, while
adding at most one deterministic third direction family. Keep exact certified
value—not policy movement—as the label, preserve the immutable blueprint, and
make no live selector claim until a precommitted rule transfers.

## Limits

Two disclosed targets are not a population or holdout. The seven-direction
library is a lower bound. A depth plateau for ordinary DCFR is evidence about
this solver, block scope, and contract; it is not proof of global opportunity
exhaustion, nor a contract-relaxation argument.
