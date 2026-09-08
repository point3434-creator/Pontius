# ADR-0190: The selector-stable affine certificate is exact and fits retained street ledgers

- Status: accepted corrected engineering result
- Date: 2026-08-21
- Implements: ADR-0189 over the unchanged ADR-0187 differential
- Clean successor preregistration commit: `119c0efc07e69bae8a7c5494c504c170002714ee`
- Result: `experiments/results/h32-selector-stable-affine-certificate-v2.json`
- Result SHA-256: `f47964cfcf91464d7db81ae68ced98b8d817ab97601a7d9deb6a00eaa71ab3cd`

## Corrected gate result

Every corrected and unchanged outcome-neutral gate passed. All six independently
recomputed warm policies had different SHA-256 digests from ADR-0186, while
their largest action-probability error was `2.220446049250313e-16` and their
largest mean information-set total variation was
`3.4368857247098436e-17`. Both are far below ADR-0179's frozen `1e-12` and
`1e-13` ceilings.

The scientific matrix was unchanged. The corrected run reproduced every v1
discrete decision signature, and the maximum difference in common selected
positive value was `4.1634e-16`. The rejected v1 artifact remains rejected;
this independently executed v2 artifact is the accepted evidence.

## Exact affine differential

The audit reconstructed all six retained targets, 36 regret-vertex public
blocks, and 216 responding-seat affine rows. Every frozen source, target,
checkpoint, blueprint, block, and direction identity passed.

All 36 fixed witnesses lay strictly inside their computed selector-stable
intervals and produced zero direct response-action flips. The affine envelope
selected 35 scales; all 35 independently completed the old exact incremental
verifier with zero response flips. Maximum absolute errors were:

| Quantity | Maximum error |
|---|---:|
| profile utility | `1.0270e-15` |
| best-response value | `1.3600e-15` |
| unilateral deviation gain | `7.9103e-16` |

This accepts the proof primitive only in its declared scope: one acting seat,
one exact public node, one common source-to-endpoint interpolation scale, and a
strict stop before the first conservative source-response tie. It does not
certify multiple changed public nodes, unions, selector switches, or chained
updates.

## Retained value diagnostic

Thirty-five of 36 affine envelopes selected. Their total positive certified
value was `5.9921299022e-6`, or `48.8025%` of ADR-0186's frozen three-family
bounded-oracle value. Per-target capture ranged from `45.6184%` to `50.0000%`.
The one abstention was acting seat 1 at `p0:bet` on panel 2 balanced, where the
affine objective was non-improving.

The approximately one-half capture is consistent with the preregistered
half-radius safety factor and downward geometric-grid quantization; it is not a
new oracle ceiling. These retained labels validate useful engineering behavior
but are not fresh selector or strategy evidence.

## Street and memory ledger

All six descriptive seat-0 ledgers fit the 15,000 ms boundary, including the
fixed 1,000 ms synchronization and emission reserve:

| Target | Charged ledger | Remaining boundary headroom |
|---|---:|---:|
| panel 1 balanced | `10,398.56 ms` | `4,601.44 ms` |
| panel 1 blocker-heavy | `9,442.41 ms` | `5,557.59 ms` |
| panel 2 balanced | `14,661.10 ms` | `338.90 ms` |
| panel 2 blocker-heavy | `12,014.95 ms` | `2,985.05 ms` |
| panel 3 balanced | `12,546.17 ms` | `2,453.83 ms` |
| panel 3 blocker-heavy | `9,450.07 ms` | `5,549.93 ms` |

The narrowest margin is real: the resident warm step alone took
`12,826.35 ms` on panel 2 balanced. A fresh rule must therefore retain a hard
deadline guard and immutable-blueprint fallback; this retained six-target fit
is not a latency-distribution claim.

Maximum GPU-pool allocation was `8,214,049,792` bytes and physical-free memory
did not fall below `7,032,799,232` bytes. The 36 fixed and 35 selected direct
teachers remained off clock. The complete differential took `241.1933 s`.

## Decision

Accept the additive selector-stable affine certificate as an exact engineering
primitive within its frozen scope. ADR-0187's advancement condition is met:
exactness passes and all retained descriptive seat-0 ledgers fit.

Authorize a separately committed fresh street trial with a predeclared
regret-vertex direction, affine-only live certificate, hard deadline, one-second
emission reserve, and immutable-blueprint fallback. Do not run the old exact
teacher on the live ledger, compose certificates, move the anchor, or infer a
strategy-quality or population claim from this retained differential.
