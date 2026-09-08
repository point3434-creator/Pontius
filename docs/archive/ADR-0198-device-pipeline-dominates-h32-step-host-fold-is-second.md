# ADR-0198: The device pipeline dominates the h32 step and host folding is second

- Status: accepted read-only engineering result
- Date: 2026-08-21
- Implements: ADR-0197
- Clean preregistration commit: `9f62521`
- Result: `experiments/results/h32-resident-step-bottleneck-profile-v2.json`
- Result SHA-256: `a8f5ed0e2b0866af4b5df0d62ddf1351ca7e8a4e9ace71223602031c1f2ae796`

## Formal result

All inherited and corrected validity gates pass. The additive v2 wrapper added
only the top-level source `passed` alias required by ADR-0197. It changed no
target, restart, timing bucket, threshold, outcome branch, or source artifact.

The run completed two already exposed timing-extreme targets, three exact
restarts per target, and 36 traverser rows in `89.30 s`. Maximum repeated-policy
probability error was `3.59e-16` and mean information-set TV was `1.14e-18`,
inside ADR-0179's numerical-identity ceilings. Maximum stage-accounting
residual was `0.467%`, so the partition is sufficiently complete for its
preregistered classification.

## Step timing

| Disclosed target | Minimum | Median | Maximum | Device share | Host-fold share |
|---|---:|---:|---:|---:|---:|
| panel-1 blocker-heavy, prior fastest | `7,139.82 ms` | `7,358.03 ms` | `7,561.82 ms` | `60.999%` | `37.035%` |
| panel-2 balanced, prior slowest | `11,305.22 ms` | `11,753.29 ms` | `11,907.93 ms` | `72.207%` | `26.478%` |

The pooled median complete step is `9,433.52 ms`; observed steps span
`7,139.82` to `11,907.93 ms`. The preregistered largest-bucket classifier is
`device_gpu` on each target and in aggregate.

## Pooled attribution

| Bucket | Six-step time | Complete-step share |
|---|---:|---:|
| Resident GPU pipeline | `38,586.28 ms` | `67.664%` |
| GPU product generation | `118.08 ms` | `0.207%` |
| Host record-to-hand fold | `17,428.18 ms` | `30.562%` |
| Transfer, including factor upload and download | `357.86 ms` | `0.628%` |
| Other host work and residual | `535.71 ms` | `0.939%` |

The important negative result is that PCIe transfer time is not the present
bottleneck. The secondary host bill is the Python/NumPy record-to-hand
aggregation after download, not moving the records itself.

Maximum CuPy-pool allocation was `7,626,233,344` bytes and physical-free GPU
memory remained at least `7,437,549,568` bytes.

## Frozen serial counterfactuals

| Counterfactual | Median projected step | Median projected speedup |
|---|---:|---:|
| 2x device-only | `6,243.94 ms` | `1.510x` |
| 4x device-only | `4,649.15 ms` | `2.031x` |
| 2x host-fold only | `7,981.17 ms` | `1.184x` |
| 2x all non-device work | `7,906.34 ms` | `1.196x` |

These are Amdahl estimates under a serial decomposition, not measurements of
another GPU or CPU. In particular, the event counters do not distinguish FP64
arithmetic throughput from device-memory bandwidth inside the resident
pipeline.

## Interpretation

“Buy a faster computer” is a technically plausible lever: most of the current
decision step is device work, and a genuine 2x acceleration of only that work
would recover roughly `3.19 s` at the pooled median. But the current RTX 5080
is already fast hardware, and this audit does not identify which replacement
architecture would deliver that workload-specific multiplier.

The `30.56%` host fold is also too large to ignore. A resident record-to-hand
reduction could attack it algorithmically and greatly shrink returned data,
but that implementation needs its own numerical and timing differential. It
is not authorized by this read-only result.

As post-result development arithmetic, deleting the measured host-fold bill
would have a `1.44x` serial ceiling. Combining that ideal deletion with a 2x
device bucket while retaining the measured transfer and other buckets gives
about `2.82x`, or `3.35 s` from the pooled median. This is more conservative
than omitting the `0.94%` other bucket, and still optimistic: an on-device fold
does work rather than vanish. It is recorded only to show why the levers may
compound, not as a frozen or measured forecast.

The slow-target maximum leaves materially less portfolio capacity than the
earlier four live samples suggested. Candidate K must therefore be priced from
the marginal batched Tier-B/Tier-C work under the complete reserve, not inferred
from the median step or a standalone affine-proof average.

## Decision

Accept the stage attribution. Follow the preregistered device-dominant branch:
next separate FP64 arithmetic pressure from device-memory/sparse-pipeline
pressure on this exact workload before recommending hardware or rewriting the
kernel. Retain device-resident record-to-hand folding as the high-value
secondary engineering screen.

Do not change the frozen live rule, 15-second boundary, immutable blueprint,
numerical tolerances, or fallback. Use this result only to price compute. It is
not a latency distribution, purchase recommendation, strategy-quality result,
deployment authorization, or composition claim.
