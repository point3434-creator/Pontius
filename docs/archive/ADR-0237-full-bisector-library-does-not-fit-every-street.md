# ADR-0237: Full bisector library does not fit every street

- Status: accepted label-free engineering result; bisector value labels remain closed
- Date: 2026-08-22
- Implements: ADR-0236
- Clean preregistration commit: `a4dceae`
- Result: `experiments/results/h32-continuation-direction-capacity-v1.json`
- Result SHA-256: `c5fab095be92757111e8ba2f668ce298eb21c3eda41ebff4f56b499dbe7a82ec`

## Formal result

Every provenance, parent, target, source-checkpoint, blueprint, warm-start,
block-partition, baseline-first order, convex-scope, five-opponent charge,
zero-own-contraction, affine-intercept, timing, memory, finite, immutable-
emission, and no-label gate passes. The clean run completed in `222.336 s`.

The artifact contains 12 one-step continuation warm states and 744 complete
six-seat affine rows: 372 retained regret vertices followed by 372 fixed
soft-regret bisectors. It executes zero certificates and serializes zero
quality rows, affine feature values, or strategy labels. Maximum affine-
intercept error is zero.

All 372 bisector endpoints differ from both their paired regret vertex and the
blueprint. The added family is therefore structurally real rather than a
duplicate-ray artifact. This says nothing about its value.

## The full second family is not street-safe

The baseline ledger—including one warm step, all 31 regret rows, the 10 ms
envelope reserve, 1,250 ms winner-proof reserve, and one-second emission
reserve—ranges from `6.858 s` to `11.630 s`, with median `8.569 s`.

Adding all 31 bisector rows raises the ledger to `10.732–19.422 s`, with median
`13.833 s`. The second family costs `3.873–7.792 s` per target, median
`5.263 s`.

Eight targets fit all 62 rows. Four do not:

| Target | Expanded ledger | Frozen prefix K |
|---|---:|---:|
| panel 2 balanced, bettor 4 | `16.102 s` | 55 |
| panel 2 blocker-heavy, bettor 0 | `17.051 s` | 53 |
| panel 2 balanced, bettor 1 | `19.422 s` | 45 |
| panel 3 balanced, bettor 2 | `17.200 s` | 48 |

Because the baseline runs first, even the tightest target finishes all 31
accepted regret rows and 14 bisector rows before its measured prefix boundary.
That partial capacity is descriptive only. ADR-0236 requires the complete
second family on every target, so it cannot be mined into a post-result subset
or used to open value labels.

Warm steps range from `718.080` to `1,595.035 ms`. Candidate rows range from
`33.604` to `1,358.706 ms`, with median `110.563 ms`. GPU-pool allocation peaks
at `6,446,538,752` bytes and physical-free memory never falls below
`8,909,750,272` bytes. Memory is not the blocker; charged affine work is.

## Decision

Retain the one-step, 31-block regret-vertex spine. Do not open a fresh bisector
value panel, select a 14-row subset from this timing result, or infer that the
bisector lacks strategy value. Capacity—not quality—rejected the full family.

Direction diversity remains viable only after a separately justified work-
reduction mechanism or a label-free structural rule that is fixed before
direction values. Prior batch measurements do not supply that mechanism.

The remaining ADR-0235 diversity branch is action width. Its next gate must be
a label-free continuation-root two-size capacity preflight: reconstruct the
embedded immutable blueprint, measure one resident warm step and the complete
widened legal block library, reserve one proof and emission, and fail closed
before any widened strategy label. Reuse the shared payoff semantics and
multi-size resident infrastructure; do not extrapolate from the earlier full-
tree action-width trials.

This is a reduced-h32 engineering result. It makes no claim about bisector
quality, action-width quality, deployment, composition, population behavior,
or broad poker strength.
