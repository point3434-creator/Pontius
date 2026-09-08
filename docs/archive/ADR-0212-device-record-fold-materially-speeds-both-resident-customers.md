# ADR-0212: The device record fold materially speeds both resident customers

- Status: accepted engineering result
- Date: 2026-08-21
- Implements: ADR-0211
- Clean preregistration commit: `f1ac132`
- Result: `experiments/results/h32-resident-record-to-hand-fold-v1.json`
- Result SHA-256: `9d26092c4974c9890dafa31681865adbdd8b5c53f56f46b73563a5cb69763a39`

## Formal result

The frozen run passes every provenance, source, numerical, structural,
accounting, memory, wall-time, immutable-emission, and no-label gate over all
six retained contexts and 36 regret-vertex blocks. The recorded invocation
ran from clean commit `f1ac132` and completed in `952.703 s`.

An initial invocation stopped before constructing the first h32 context because
the shell had not initialized `PONTIUS_CUDA_DLL_DIRECTORY`. It wrote no result.
The recorded invocation supplied the repository-pinned CUDA 13 DLL directory
from `RUNBOOK.md` and changed neither code nor configuration.

The largest complete-warm-step errors against the accepted host teacher are:

- regret accumulator: `5.551115123125783e-16`;
- strategy-sum accumulator: `0.0`;
- current-policy probability: `3.3306690738754696e-16`; and
- mean information-set total variation: `1.4839939776138963e-18`.

Across every Tier-B cell and repetition, the maximum affine coefficient error
is `3.116062963215427e-12`, the maximum reconstructed-composite error is
`4.335538140521136e-18`, and all structural fields agree exactly. This is
ADR-0179 numerical identity; no bitwise output claim is made.

Memory remains safe. CuPy-pool allocation peaks at `8,702,849,024` bytes and
physical-free device memory never falls below `6,357,516,288` bytes.

## Both customers clear promotion

The pooled complete-step medians are:

| Customer | Host fold | Device fold | Speedup |
|---|---:|---:|---:|
| six-traverser warm step | `9,716.659 ms` | `6,716.432 ms` | `1.446699x` |
| selected Tier-B topology | `4,130.848 ms` | `3,265.804 ms` | `1.264880x` |

Every retained target improves. The target-wise warm-step speedups range from
`1.3473x` to `1.5764x`; none regresses. The globally selected Tier-B cell is
`device_batch`, chosen by the frozen lower-pooled-median rule. It improves on
its host-batch peer at every target and clears the `1.05x` materiality rule
without a `2%` target regression. Accept the device fold at both warm-step and
Tier-B call sites.

The placement differential explains the gain directly. Across the 18 measured
warm samples, moving the fold removes `53,284.335 ms` of host fold and reduces
device-to-host time from `1,045.301 ms` to `24.710 ms`; it adds only
`99.234 ms` of device fold and `338.394 ms` of host finalization. Output
transfer falls from `7,939,229,472` to `11,005,632` bytes, approximately
`721x`.

Across the 18 host-batch/device-batch Tier-B samples, moving the fold removes
`15,014.935 ms` of host fold and reduces device-to-host time from
`321.986 ms` to `22.090 ms`; it adds `45.649 ms` of device fold and
`102.197 ms` of host finalization. Output transfer falls from `2,194,588,800`
to `3,041,280` bytes. Batch wall totals fall from `74,754.568 ms` to
`59,319.797 ms`, a `1.2602x` aggregate reduction consistent with the pooled
median result.

This is the requested composable ledger: host milliseconds removed, device
milliseconds added, residual host work, transfer time, and bytes are separate
line items rather than one opaque delta.

## H3 is rejected by intervention

Removing the inter-call host fold barrier does not resurrect six-way batching
as a material optimization. Per-target host batching speedups are
`1.0065x` to `1.0427x`; device batching speedups are `1.0021x` to `1.0176x`.
The device-versus-host interaction ratios are `0.9760x` to `1.0036x`, far
below ADR-0211's joint `1.10x` device-speedup and `1.08x` interaction rule.

The frozen global rule still chooses `device_batch` because its pooled median,
`3,265.804 ms`, is slightly below `device_scalar` at `3,272.755 ms`. That
`1.0021x` difference is a deterministic topology choice, not evidence that
batching solves K. The cross-candidate packing hypothesis remains rejected.

## Repriced 15-second ledger

| Retained context | Device warm | Device Tier B | Complete ledger | Headroom |
|---|---:|---:|---:|---:|
| panel 1 balanced | `5,587.9 ms` | `2,888.4 ms` | `9,937.0 ms` | `+5,063.0 ms` |
| panel 1 blocker-heavy | `5,027.0 ms` | `2,616.1 ms` | `9,153.6 ms` | `+5,846.4 ms` |
| panel 2 balanced | `9,099.4 ms` | `4,326.0 ms` | `14,914.5 ms` | `+85.5 ms` |
| panel 2 blocker-heavy | `7,859.4 ms` | `3,802.3 ms` | `13,164.0 ms` | `+1,836.0 ms` |
| panel 3 balanced | `7,923.3 ms` | `3,642.3 ms` | `13,063.6 ms` | `+1,936.4 ms` |
| panel 3 blocker-heavy | `4,796.9 ms` | `2,508.8 ms` | `8,789.9 ms` | `+6,210.1 ms` |

All six complete current-library ledgers fit, and the report-only linear K
estimate reaches six on every target. Panel 2 balanced has only `85.5 ms` of
measured headroom, so this closes the retained development ledger but does not
establish a robust deployment latency distribution. No fresh selector label
is opened by this result, and the emitted policy remains the immutable
blueprint.

Charging one additional complete device-fold warm step against the same
measured ledger would fit only panel 1 blocker-heavy (`+819.4 ms`) and panel 3
blocker-heavy (`+1,413.2 ms`). It would miss the other four contexts. A second
step is therefore a possible context-gated scheduler arm, not a universal live
rule, and would require its own prospective strategy protocol.

## The next bottleneck is now sharper

After the fold move, the resident sparse GPU pipeline accounts for
`118,722.200 ms` of `121,161.764 ms` across measured device warm steps
(`97.987%`). In device-batch Tier B it accounts for `48,132.782 ms` of
`59,319.797 ms` (`81.141%`); selector reverse is `10.027%` and affected-term
preparation is `7.886%`. Device folding itself is below `0.1%` in both
customers.

Feature-width fill is only a workload proxy. It cannot distinguish FP64
arithmetic, sparse-memory pressure, or launch/occupancy limits. Nsight Compute
2026.2.1 is available, as recorded non-gating by the artifact. The next
engineering experiment should therefore be a separately preregistered,
single-call hardware profile of representative resident sparse passes. It must
not reuse hardware counters inside paired timing and must make no strategy or
hardware-purchase claim.

## Decision

Promote the device record-to-hand fold at both the complete warm-step and
Tier-B call sites. Preserve the globally selected device-batch topology for the
current six-block ledger, while retaining ADR-0210's conclusion that batching
itself is not a material optimization. Treat all-six fit as a retained
development result; the `85.5 ms` minimum headroom is not a deployment margin.

Before changing the resident sparse implementation, preregister and run a
separate non-gating Nsight Compute profile that distinguishes arithmetic,
sparse-memory, and launch/occupancy pressure. Keep fresh action-conditioned
strategy labels sealed until that engineering profile is interpreted and the
next complete-ledger choice is frozen.

This result makes no strategy-quality, opportunity-distribution, transfer,
deployment, population, composition, occupancy, roofline, or hardware claim.
