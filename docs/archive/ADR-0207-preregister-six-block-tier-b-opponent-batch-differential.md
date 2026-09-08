# ADR-0207: Preregister the six-block Tier-B opponent batch differential

- Status: accepted engineering preregistration before any h32 batch measurement
- Date: 2026-08-21
- Depends on: ADR-0179, ADR-0198, ADR-0205, and ADR-0206
- Config: `experiments/configs/h32-tier-b-opponent-batch-v1.json`
- Config SHA-256: `0b3009edbd3b187f10efa837e454847486b0066a6e80c94ebe1b237cff69fe56`
- Batch primitive: `src/pontius/batched_selector_stable_affine_response.py`
- Batch primitive SHA-256: `d5d9203dffb33124fd35cecebe388975b5eea2ebfb981eebf8e434b0723a2e4e`
- Batch control: `tests/test_batched_selector_stable_affine_response.py`
- Batch-control SHA-256: `df87f42f201d67ee9008bdb9f71b54b5391fcb5c8a9512c2e6741be41eed62b5`
- Audit: `src/pontius/h32_tier_b_opponent_batch_differential.py`
- Audit SHA-256: `96d0de5d34d717f8245512e4cf7a7e672f3ec7c731724b5826a361661b29fb9e`
- Audit control: `tests/test_h32_tier_b_opponent_batch_differential.py`
- Audit-control SHA-256: `a4e5f0d80ef36f2668da0d172a865d02175a5c08a0de9ecc7d11641b77609794`

## Question

ADR-0206 identifies the exact objective-slope-times-cap-radius composite as a
near-perfect retained-label opportunity locator and rejects the own-slope
Tier-A prefilter. Tier B is therefore unavoidable. Can its five
opponent-BR-conditioned directional reads be shared across all six coherent
regret-vertex blocks cheaply enough to remove K as the retained street
bottleneck, without changing one coefficient or selector boundary?

This is an implementation differential, not another selector fit. It loads no
strategy label and makes no strategy-quality claim.

## Frozen algebra and charge boundary

Retain one regret-vertex public-node block per acting seat, ordered seats zero
through five, on each of ADR-0206's six retained contexts.

For a candidate editing only seat `i`, `BR_i` is invariant to seat `i`'s own
policy. The acting-seat row therefore uses the accepted zero-terminal-
contraction affine reverse. Its host work is measured separately; it is not
hidden inside the batch or declared literally free.

For every responding seat `j`, pack the five candidates whose acting seat is
not `j` into one heterogeneous resident contraction over the shared belief,
incidence operators, and seat-`j` automaton cache. This gives exactly:

- 30 scalar opponent calls in the teacher arm;
- six batched opponent calls in the treatment arm; and
- 30 semantic opponent rows in both arms.

The charged opponent work includes term preparation, factor upload, product
generation, the resident sparse pipeline, download, host hand fold, and five
reverse selector passes. The `u_j` and `BR_j` directional terms come from the
same contraction; no separate full endpoint evaluation is allowed.

The reduced h3 control already requires the batch to match independent scalar
rows and rejects own-seat leakage into the opponent path. The h32 run remains
the first measurement of this implementation on the target geometry.

## Teacher and numerical identity

For every target, candidate, and responding seat, compare:

- utility, best-response, and deviation-gain intercepts and slopes;
- selector-stable radius;
- first-switch information set, actions, and hand;
- selector comparison and exact-tie counts; and
- affected, reused, and complete terminal counts.

All numeric differences must be at most `2e-11`; every structural field must
match exactly. This is ADR-0179 numerical identity. Policy digests remain
diagnostics because the warm step and GPU reductions may reassociate.

Also reconstruct the complete six-row coefficient vector per candidate and
require the Tier-B composite to match the scalar teacher to `2e-11`. Speed,
value magnitude, winner identity, and full-set fit are not validity gates.

## Timing and memory protocol

Each retained target receives one exact warm resident step and the same six
regret vertices. Warm each timing arm once. Then measure three paired
repetitions with arm order:

```text
scalar, batched
batched, scalar
scalar, batched
```

Release only unreferenced CuPy pool blocks and synchronize at every arm
boundary. Report arm wall time plus every exposed device, transfer, reverse,
and fold component. Use medians for the decision ledger and retain all samples.

Before the first full batch on each context, physical-free GPU memory must be
at least `5,184,456,164` bytes, the frozen non-cache reserve derived in the
resident-cache lineage. If not, stop before the batch and write a rejected
result. During work, pool allocation must remain at most `12,000,000,000`
bytes and post-work physical free at least `1,000,000,000` bytes. This is a
headroom gate, not an invitation to catch and continue after an OOM.

## Complete B-to-C ledger

For each target charge exactly once:

1. the observed complete warm step;
2. construction of all six regret-vertex endpoints;
3. all six zero-contraction acting-seat rows;
4. the median six-call batched opponent arm;
5. ranking plus one winner affine envelope; and
6. the frozen one-second emission reserve.

Report whether the complete six-block set fits `15,000 ms` and its signed
headroom. Emit only the immutable blueprint. The causally selected winner and
its affine envelope are diagnostics; no exact strategy label is opened or
created.

## Predictions and branches

Register two report-only predictions:

1. the batch is numerically identical and reduces opponent wall time by about
   `3x` to `5x`; and
2. where that speedup reaches at least `3x`, the complete six-block B-to-C
   ledger fits the observed retained street.

They cannot rescue a failed identity or memory gate.

- If identity, accounting, provenance, or headroom fails, reject the batch and
  preserve the scalar path.
- If the batch passes and all six complete ledgers fit, accept B-to-C as the
  retained engineering shape and move the next software differential to the
  resident host fold; its recovered time then buys search depth.
- If the batch is exact and faster but any complete ledger does not fit,
  continue Tier-B fusion or chunk-width engineering before fresh selector
  labels.
- If the batch is not faster, retain the scalar implementation and reprofile
  before changing kernels.

No branch authorizes deployment, population inference, composition, hardware
selection, widened-corpus transfer, or strategy-quality claims. The next
strategy-facing test remains a separately frozen action-conditioned,
single-family widened corpus.
