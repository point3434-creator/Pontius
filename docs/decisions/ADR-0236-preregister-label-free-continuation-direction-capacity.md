# ADR-0236: Preregister label-free continuation direction capacity

- Status: accepted preregistration before any bisector affine row or strategy label
- Date: 2026-08-22
- Follows: ADR-0235
- Config: `experiments/configs/h32-continuation-direction-capacity-v1.json`
- Config SHA-256: `2f7a3d4206c2a5f906f0d3a67afaa596f59c6f6b064f19f3f961d4902349244c`
- Implementation: `src/pontius/h32_continuation_direction_capacity.py`
- Implementation SHA-256: `7ddb73e3ca47c272212d51e754bfa7aaafcf7ac9382643b1b1a639cfa621dca3`
- Control test SHA-256: `54fd7ffdc240a114f23a3d1e29a4d3c96bd33cfd1752cca74542f33ced4bd111`

## Question

ADR-0235 rejects a second ordinary continuation DCFR step: it adds 14.00% to
the charged ledger, reproduces the same winner on 11 of 12 held-out targets,
and lowers exact value per charged second. Can the retained one-step state
instead support one coherent additional direction ray across every legal
continuation block while preserving the complete regret-vertex library, one
winner-proof reserve, the emission reserve, and the 15-second boundary?

This is a capacity question only. It does not ask whether the added direction
contains value.

## Why direction diversity precedes action widening

Generator weakness has replicated: soft one-step movement captures only about
5% of the bounded vertex opportunity, while ordinary depth does not repair it.
The prior immutable-blueprint best-response vertex was directionally redundant,
but that does not establish library completeness. Action widening remains a
separate branch; its earlier scale-1 candidates were cap-bound, and it requires
a wider game and resident state. The lower-risk next test is therefore an
additional ray derived from the already-paid one-step state with no new cache.

## Frozen added family

Use the exact sealed Latin-C/D targets from ADR-0234 and reconstruct one
continuation-root solver from each immutable restricted average-64 blueprint.
Run exactly one device-fold DCFR step. For each of the 31 legal continuation
public-node blocks construct:

1. the retained pure instantaneous-regret vertex; and
2. a fixed soft-regret bisector whose selected information-set rows are the
   equal-weight midpoint of the one-step soft current policy and that block's
   regret vertex, with every off-block row equal to the blueprint.

The mixture weight is fixed at `0.5` before measurement. There is no weight
grid, label-informed mixture, adaptive direction construction, or second
solver step. Each endpoint changes one acting seat at one exact public node
and is a convex source-relative ray.

## Baseline-first ledger

Price all 31 regret-vertex rows in continuation preorder before any bisector
row, then price all 31 bisector rows in the identical block order. This ordering
protects the accepted spine: a later hard clock can always retain the complete
baseline library before considering direction diversity.

Each row computes the acting-seat affine identity and all five charged
opponent-BR-conditioned coefficients. Serialize only endpoint identity,
structure, contraction counts, elapsed cost, intercept error, and memory—not
the affine coefficients or any quality value.

For each target calculate both ledgers before any label exists:

```text
one resident warm step
+ measured candidate rows in frozen baseline-first order
+ 10 ms affine-envelope reserve
+ 1,250 ms independent winner-proof reserve
+ 1,000 ms synchronization/emission reserve
```

The screen always measures all 62 rows off clock. Profiled capacity is a
development measurement, as in ADR-0226; a future strategy trial must restore
the hard pre-row and pre-proof guards and immutable fallback.

## Frozen promotion rule

Authorize a separate fresh bisector value preregistration only if, on every
target:

- the complete measured 62-row ledger is at most 15 seconds; and
- all 31 bisector endpoint digests differ from both their paired regret vertex
  and the blueprint.

Otherwise retain the one-family regret-vertex spine and do not open direction
labels. Report conservative worst-case K as a diagnostic, not a promotion
requirement; ADR-0226 already established that repeated-maximum costing is too
conservative to represent the deterministic full-library path.

## Outcome-neutral gates and claims boundary

Require clean committed execution, accepted source and manifest parents, exact
held-out target identity, 12 warm steps, 31 blocks and 992 information sets per
target, 744 candidate rows, 744 own rows, 3,720 opponent rows, baseline-first
order, convex scope, five-opponent charge, zero own contractions, numerical
warm identity, affine-intercept identity, finite timings, the 12 GB GPU-pool
ceiling, 1 GB physical-free floor, blueprint-only emission, and no labels.

Do not gate validity on elapsed fit, endpoint distinctness, candidate cost,
position, or any uncomputed strategy outcome. Those quantities decide only the
next branch after the mechanism gates pass.

This screen executes no exact certificate, serializes no affine opportunity
value or quality vector, populates no strategy, and makes no strategy-quality,
deployment, composition, population, or broad poker-strength claim.

## Decision

Commit this ADR, config, additive implementation, and controls before the first
bisector affine row. Run once from that clean preregistration commit. If the
expanded library passes the frozen capacity rule, preregister its value test on
fresh posteriors; do not infer value from capacity.
