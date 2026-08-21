# ADR-0199: Preregister the retained affine selector-cascade replay

- Status: accepted preregistration before missing-feature extraction or semantic label load
- Date: 2026-08-21
- Depends on: ADR-0186, ADR-0179, ADR-0190, and ADR-0198
- Config: `experiments/configs/h32-retained-affine-selector-cascade-replay-v1.json`
- Config SHA-256: `9f700db8c7ddedf9e3d0e91f982634b41d65483719735b7d6be202294ffec841`
- Runner: `src/pontius/h32_retained_affine_selector_cascade_replay.py`
- Runner SHA-256: `04062b4355d773ee7046995b05f03c927c8ecdae8edf5576819e642f8e948d0e`
- Control test: `tests/test_h32_retained_affine_selector_cascade_replay.py`
- Control-test SHA-256: `31a6d43bb936583d47d54eec3fb5f1758151af5738f890eeb9018ffedf774b29`

## Question

Can the already sealed h32 contexts support a causal, clock-priced opportunity
selector when candidates are ranked by their own affine coefficients rather
than the failed regret-mass and action-gap proxies?

This is a development replay. It may identify a useful feature or expose a
library/cost limit, but it cannot provide fresh strategy evidence.

## Feature extraction is not a new label campaign

ADR-0186 already sealed exact adaptive-search labels for six public-node blocks
and three direction families per target. ADR-0190 computed complete affine rows
only for the regret-vertex direction. Reconstruct the same six contexts under
ADR-0179, then compute the missing soft-DCFR and blueprint-BR-vertex affine
coefficients for every row under one fixed feature specification.

The label artifact's bytes must be read during config validation to confirm its
sealed SHA-256. That opaque integrity read is not represented as label
blindness. The semantic barrier is narrower and testable: do not deserialize
the label JSON, attach a prior probe feature, inspect a per-row value, select a
feature, or derive K until all `108` candidate feature rows and every
label-independent capacity row exist in memory. Only then deserialize and join
all frozen fields in one pass.

No feature family may be added, removed, or selectively recomputed after the
join. No new exact certificate, adaptive scale search, teacher value, target,
policy step, or strategy-quality label may run.

## Candidate strata

Score three separate within-target matrices:

1. **Primary — regret vertex only:** six blocks per target. This is the current
   deployment-shaped direction family and the only clean block-location test.
2. **Secondary — all families:** six blocks by three families, or 18 candidates
   per target. Its K can bind, but success is weak evidence because a ranker can
   look good merely by rejecting already dominated soft directions.
3. **Family-confound control — soft excluded:** the 12 regret- and BR-vertex
   rows. If an apparent 18-set advantage disappears here, classify it as family
   discrimination rather than opportunity location. The control still contains
   near-duplicate vertex policies and cannot replace a widened fresh corpus.

Never pool the 36 regret blocks across targets and call the result live top-K.
Report pooled correlations only as descriptive cross-context diagnostics.

## Frozen cascade and features

For an edit confined to acting seat `i`, `BR_i` is invariant to seat `i`'s own
policy. Therefore

```text
d gain_i / ds = -d u_i / ds
```

is exact inside the affine scope. Tier A ranks by the resulting own-gain
improvement slope. Record its present zero-terminal-contraction reverse cost,
and separately report the diagnostic capacity if a later live step exposes the
same coefficient from retained warm telemetry at zero marginal reverse cost.
The latter is not yet an implemented speedup.

Tier B charges exactly the five opponent-BR-conditioned calls. Report their
terminal-contraction, reverse-evaluation, and remaining overhead milliseconds
separately. Compute:

- the exact anchor NashConv improvement slope under the positive-part rule used
  by the affine envelope;
- the cap-only radius, as the minimum positive-slope cap budget divided by that
  slope, clipped to `[0, 1]` and deliberately omitting selector stability; and
- the composite `max(0, objective improvement slope) * cap radius`.

The existing affine primitive also returns selector-stability intervals during
the opponent reverse passes. Tier C may therefore reuse those rows and reserve
only one measured envelope cost for the winner; do not invent a second full
endpoint bill. Record cap-radius overshoot relative to the selector-stable
radius as the frozen miss-localization diagnostic.

The complete feature list is:

- regret mass;
- negative minimum action gap;
- prior regret-vertex probe cap radius;
- prior regret-vertex probe positive value;
- exact Tier-A own-gain improvement slope;
- exact Tier-B NashConv improvement slope;
- Tier-B cap radius; and
- Tier-B slope-predicted value.

The two prior probe fields repeat at block level across families in the 18- and
12-sets. They are benchmarks, not newly family-specific features.

## Clock-derived K

Derive K independently per target and candidate stratum before the label join.
Start from 15,000 ms; subtract the measured warm step, the frozen 1,000 ms
emission reserve, the cost of constructing and extracting Tier A for every row
in the stratum, and one maximum measured envelope cost. Divide the remainder by
the maximum measured opponent-row wall cost in that target and stratum, floor,
and cap by library cardinality.

Report two K values:

- **current K**, charging the zero-contraction Tier-A reverse path that exists
  today; and
- **warm-reuse diagnostic K**, setting only that reverse cost to zero while
  retaining endpoint construction and every measured Tier-B/Tier-C bill.

If K reaches six in the primary set, call it library-limited. Recall at six is
then tautological and cannot count as selector evidence. The fixed diagnostic
K ladders remain report-only and do not replace the capacity-derived K.

## Scoring

Within each target, rank high feature first with acting seat, public history,
and frozen family order as the structural tie-break. For every feature and K,
report:

- canonical-best recall;
- best exact retained value present in top-K;
- per-target capture fraction;
- pooled value-weighted capture;
- exact random-ranking recall and expected-value floors; and
- the clairvoyant ceiling.

Also run the actual cascade: Tier A selects K, the Tier-B composite chooses one
survivor, and only that survivor is treated as the Tier-C selection. Report its
retained certified value per conservatively charged second. A one-raw-guard
materiality/no-op census is descriptive only; ADR-0194 already forbids turning
that exposed threshold into a live rule on this corpus.

## Required mutation controls

The run is invalid unless both controls pass:

1. Charge five opponent-BR rows. A six-row charge or an acting-row terminal
   contraction must fail.
2. Validate the Tier-A precondition, not merely the algebra. A deterministic
   two-action control first proves the identity for an own-seat-only edit, then
   perturbs one off-seat node and requires the free-path slope to disagree with
   the endpoint teacher. The impure direction must be rejected.

These controls guard future block-boundary or shared-index refactors that could
silently turn an exact feature into an approximation.

## Predictions and evidence boundary

Freeze two report-only predictions:

1. the slope-times-radius composite wins pooled value-weighted recall, with its
   misses concentrated where cap radius overshoots selector stability; and
2. Tier A clears value recall at K at least eight only in the weak secondary
   18-set. The six-candidate primary corpus cannot test that statement.

Neither prediction is a validity gate. Pass/fail depends only on provenance,
complete feature extraction before semantic label load, numerical identity,
scope and charge controls, finite arithmetic, time/memory ceilings, and
blueprint-only emission.

## Decision

Run once from a clean preregistration commit. Accept a passing result only as a
retained-context selector and cost diagnosis. Do not make a strategy-quality,
deployment, composition, or fresh-transfer claim.

After sealing the result, schedule the resident-fold differential already
identified by ADR-0198. That later preregistration must report host milliseconds
removed and device milliseconds added separately, derive delta explicitly, and
use ADR-0179's frozen numerical ceilings with digests diagnostic only. CUDA
graphs remain conditional on the post-fold profile becoming launch-bound.
