# ADR-0194: The affine street mechanism transfers to seat 5 but value remains concentrated

- Status: accepted prospective replication result
- Date: 2026-08-21
- Implements: ADR-0193
- Clean preregistration commit: `6d65637400e58adf73de83cd9f0dac7db977e23d`
- Result: `experiments/results/h32-fresh-selector-stable-affine-street-seat5-v1.json`
- Result SHA-256: `a36e3b6181e412ccf339ab42fe694b0f3b04b0aa60872c498e29bf9e41bfb3cf`

## Formal result

Every inherited and successor gate passed. All four fresh target and descriptor
digests were absent from the sealed ADR-0192 commit. The wrapper preserved the
complete hash-bound seat-0 live core and changed only target seat 4 and acting
seat 5.

All four live paths began construction and the affine proof, selected before
the 14,000 ms cutoff, and simulated a non-blueprint seat-5 emission. All four
fixed and selected-scale exact teachers ran only after emission was frozen and
reported zero response-action flips. Maximum absolute errors were:

| Quantity | Maximum error |
|---|---:|
| profile utility | `1.1102e-16` |
| best-response value | `1.1102e-16` |
| unilateral deviation gain | `1.8041e-16` |

The fixed acting-seat-5 substitution therefore transfers the certificate,
causal ordering, and live runtime mechanism on this second fresh panel.

## Fresh value

| Target | Selected scale | Exact positive certified value | Blueprint NashConv fraction |
|---|---:|---:|---:|
| panel 1 blocker-heavy | `2^-1` | `7.9965715e-11` | `1.0777e-9` |
| panel 2 balanced | `2^-1` | `8.7994669e-7` | `1.1277e-5` |
| panel 3 balanced | `2^-1` | `2.4004762e-10` | `3.7700e-9` |
| panel 3 blocker-heavy | `2^-1` | `8.1391319e-8` | `1.6169e-6` |

Total exact positive certified value was `9.6165801794e-7`; the live affine
prediction differed by `1.11e-16` in aggregate. Every source-selector interval
and cap/objective limit reached scale one, so the half-radius rule selected
`0.5` on all four targets. The two microscopic outcomes arise from shallow
objective slopes, not narrow safety regions.

Value is more concentrated than at seat 0. Panel 2 balanced supplies `91.50%`
of the seat-5 total, and the largest target value is `11,004x` the smallest.
Non-blueprint emission count is again a poor proxy for useful value.

## Live timing and memory

| Target | Warm step | Construction | Affine proof | Complete street ledger | Boundary headroom |
|---|---:|---:|---:|---:|---:|
| panel 1 blocker-heavy | `6,978.55 ms` | `140.09 ms` | `225.62 ms` | `8,382.91 ms` | `6,617.09 ms` |
| panel 2 balanced | `10,935.26 ms` | `143.80 ms` | `313.71 ms` | `12,430.57 ms` | `2,569.43 ms` |
| panel 3 balanced | `9,754.49 ms` | `143.15 ms` | `290.35 ms` | `11,226.83 ms` | `3,773.17 ms` |
| panel 3 blocker-heavy | `7,043.21 ms` | `144.36 ms` | `230.99 ms` | `8,457.08 ms` | `6,542.92 ms` |

Every ledger includes the fixed one-second reserve. Maximum GPU-pool allocation
was `7,626,233,344` bytes, physical-free memory remained at least
`7,437,549,568` bytes, and the complete run with off-clock teachers took
`97.5289 s`.

## Combined extreme-seat evidence

Across ADR-0192 and this replication:

- all eight fresh fixed-rule paths complete before the hard deadline;
- all eight affine selections match the old exact verifier with zero flips;
- total exact positive certified value is `2.0879628587e-6`; and
- the two largest targets supply `88.78%` of that total.

A retrospective one-raw-guard materiality filter (`3e-9`) would retain five of
eight emissions and `99.9021%` of their exact value. That observation is not a
frozen rule or validation result: it is computed after both panels were
revealed and may only motivate a separately preregistered transfer test.

## Interpretation

The online spine now has prospective mechanism evidence at both order extremes.
The selector-stable affine proof, deadline accounting, and blueprint fallback
are no longer the immediate weak link. The remaining issue is identifying or
screening material opportunity: safe positive directions are common in these
panels, but useful value is sparse and highly target-dependent.

This remains eight constructed h32 river beliefs on three boards. It is not a
latency distribution, middle-seat result, opponent-performance result, poker
strategy-quality claim, deployment authorization, or certificate-composition
rule.

## Decision

Accept the acting-seat-5 replication and preserve the live core unchanged.
Stop consuming the now-exposed local-blocker family merely to accumulate more
4-of-4 counts.

Before another fresh GPU panel, freeze a broader transfer design: new board or
belief regimes, explicit position coverage, and a causally available
materiality/no-op rule whose threshold has principled provenance. Treat the
one-raw-guard retrospective as development evidence only. Do not tune a
threshold and report it on these eight targets as prospective evidence, and do
not return to another DCFR variant while opportunity magnitude is unresolved.
