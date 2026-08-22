# ADR-0206: Opponent-sensitivity composite locates retained value but the Tier-A cascade fails

- Status: accepted retained-label development result
- Date: 2026-08-21
- Implements: ADR-0205 under the scientific contract of ADR-0199
- Clean preregistration commit: `5f13161`
- Result: `experiments/results/h32-retained-affine-selector-cascade-direct-v1.json`
- Result SHA-256: `7b251d25b3befcdf2bb5b66dfd6c4ed78818da43f53d5a70e7cdf220d4b6cd93`

## Formal result

The reviewed direct replay passes every inherited gate. It deterministically
reconstructed all six retained ADR-0186 targets, completed one exact warm step
per target, extracted all features before loading the sealed labels, and then
joined 108 candidate rows and 648 responding-seat affine rows to those labels.
The run made exactly 540 charged opponent-BR-conditioned calls: five, not six,
for each candidate.

The acting-seat identity and its scope guard both have teeth. The maximum pure
acting-seat identity error is zero. A deliberately contaminated direction
changes one off-seat node and produces the required `0.2` disagreement between
the free identity and the endpoint teacher. Maximum warm-start probability
error is `2.22e-16`; mean information-set TV is `3.44e-17`. The maximum affine
intercept error is zero. All values are inside ADR-0179's numerical ceilings.

No fresh label was generated. The semantic label load occurred only after the
complete feature matrix and label-independent capacity arithmetic existed.
The emitted policy remained the immutable blueprint.

## Primary six-block result

The deployment-shaped primary set contains one regret-vertex direction for
each of six public-node blocks per target.

| Feature | Pooled Spearman | Mean within-target Spearman | Recall@1 | Pooled value capture@1 |
|---|---:|---:|---:|---:|
| exact Tier-B slope x cap-radius composite | `0.991763` | `1.000000` | `6/6` | `100.000%` |
| cap radius alone | `0.337569` | `0.273375` | `3/6` | `95.415%` |
| exact objective-improvement slope alone | `0.135393` | `0.009524` | `1/6` | `2.928%` |
| exact Tier-A own-gain slope | `-0.102445` | `-0.152381` | `1/6` | `2.952%` |
| regret mass | `-0.080051` | `-0.152381` | `1/6` | `2.654%` |
| negative minimum action gap | `-0.209524` | `-0.180952` | `0/6` | `2.471%` |

The composite selects the exact best block in every retained context. Radius
alone captures most pooled value but does not identify half of the per-target
winners; slope alone is poor. Their product is therefore the identified
quantity on this matrix.

This is retained-panel evidence that opportunity is radius-dominated: useful
blocks are distinguished primarily by low opponent sensitivity, which gives a
modest own-value slope room to accumulate safely. It is consistent with the
`1,024x` radius variation and the 75 cap-bound, zero objective-bound searches
reported prospectively by ADR-0186. It is not a claim that radius dominates in
all poker contexts.

The preregistered prediction that the composite would win holds. The predicted
localization of its misses at selector-window overshoots cannot be tested:
there are no primary top-one misses. It is neither confirmed nor falsified.

## Family-confound control

The result is not merely a classifier that learned to avoid soft DCFR.

| Candidate set | Composite pooled Spearman | Mean within-target Spearman | Value capture@1 | Recall / capture@2 |
|---|---:|---:|---:|---:|
| all 18 rows | `0.993676` | `0.979334` | `99.999999996%` | `100% / 100%` |
| soft-excluded 12 rows | `0.991179` | `0.988009` | `99.999999996%` | `100% / 100%` |

Top-one recall is `3/6` on both secondary sets only because regret and
best-response vertices are material near-duplicates with deterministic
canonical tie ordering. Top-two resolves every target. Because the composite
survives removal of every soft row, its advantage is opportunity localization,
not just direction-family discrimination.

## The proposed cascade is rejected

Tier A is exact but not sufficient. At K=8 on the soft-excluded control it
captures `80.407%`, below the `91.918%` random-ranking expectation, with recall
`4/6`. The preregistered Tier-A-at-K prediction is therefore falsified on the
clean control.

Capacity derived before label join also shows that the six-block primary set
does not saturate under the current 15-second ledger:

| Target order | Current K | Warm-reuse K | Current selected-value capture |
|---|---:|---:|---:|
| panel 1 balanced | 3 | 4 | `49.341%` |
| panel 1 blocker-heavy | 5 | 5 | `100.000%` |
| panel 2 balanced | 1 | 1 | `0.000%` |
| panel 2 blocker-heavy | 2 | 2 | `100.000%` |
| panel 3 balanced | 1 | 2 | `36.972%` |
| panel 3 blocker-heavy | 5 | 5 | `100.000%` |

The pooled current-clock capture is `78.169%`; warm Tier-A reuse raises it only
to `78.745%`. That pooled number is concentration-sensitive and must not hide
the zero and partial per-target rows. Across all 108 candidates the five
opponent rows cost a median `529.493 ms` and a maximum `1,823.046 ms`; terminal
contractions account for median `410.602 ms`. The conservative per-target
maximum used to price K ranges from about `1.17 s` to `1.80 s` per candidate.
Tier B, not Tier A, is the selector-capacity bottleneck.

On all 18 families the literal Tier-A-first cascade captures only `2.546%` of
pooled value; on the soft-excluded control it also captures `2.546%`. The free
prefilter removes the rows that the exact composite would select. Exactness of
a feature does not make it a useful ranker.

## Decision

Accept the exact Tier-B slope-times-radius composite as a strong retained-label
opportunity locator. Reject Tier A as a filtering stage. Preserve its algebra:
own-seat BR invariance and the free profile-utility slopes should be absorbed
inside a simplified B-to-C path, not used to exclude candidates.

Before a fresh selector trial, preregister an engineering differential that
prices the trimmed five-opponent directional work and a heterogeneous batched
pass over all six primary blocks using the shared resident operators. The
target live shape is: compute Tier B for every coherent block that fits, rank
by the composite, and spend Tier C on the winner. Derive K from measured
capacity again; do not assume a `3x` to `5x` speedup or six-block saturation.

The resident-fold differential remains valuable, but its recovered time buys
search depth only after Tier-B selection ceases to bind. Keep host milliseconds
removed and device milliseconds added as separate ledger entries under
ADR-0179's numerical ceilings.

This result authorizes no strategy-quality, fresh-transfer, deployment,
composition, population, or broad opportunity-distribution claim. The next
scientific test remains a widened, single-direction, action-conditioned corpus
with labels held fresh.
