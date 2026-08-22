# ADR-0210: Six-way Tier-B batching is exact but does not reduce resident contraction work

- Status: accepted corrected engineering result
- Date: 2026-08-21
- Implements: ADR-0207 and ADR-0209
- Clean preregistration commit: `4c18a65`
- Result: `experiments/results/h32-tier-b-opponent-batch-v2.json`
- Result SHA-256: `84ed32019afeaa4a18695436c74e41722fc146044a2150de92323833cb8d42fd`

## Formal result

The corrected run passes every frozen provenance, source, identity, accounting,
memory, and no-label gate over all six retained contexts and 36 regret-vertex
blocks. It compares 30 scalar opponent rows with six responding-seat batch
calls in each timing arm. The maximum coefficient error is
`1.8076651286946799e-12`, the maximum reconstructed-composite error is
`1.4372031532537341e-18`, and all structural fields agree exactly. Warm policy
reconstruction remains inside ADR-0179 with maximum probability error
`2.220446049250313e-16` and maximum mean information-set total variation
`3.4368857247098436e-17`.

The memory gates also pass. CuPy-pool allocation peaks at `8,702,849,024`
bytes and physical-free device memory never falls below `6,357,516,288` bytes.
The complete audit takes `358.754 s`. It loads no strategy label and emits only
the immutable blueprint.

## Timing result

Reducing the Python/API call count from 30 to six does not materially reduce
the charged work. Target-wise speedups range from `0.998895x` to `1.028844x`,
with median `1.005881x`. The preregistered `3x` to `5x` prediction is cleanly
falsified.

Across all 18 measured batch samples, batch wall time totals `75,165.774 ms`
versus `75,785.612 ms` for the paired scalar samples. More importantly, the
terminal-contraction bucket is `64,349.671 ms` batched versus `64,686.909 ms`
scalar: batching retains `99.479%` of that bill. The batch performs 5,760
affected terminal contractions through 2,973 width-limited sparse passes.

The measured batch wall time decomposes as follows. These totals are additive
over the 18 samples; the residual is only `0.204%`.

| Batch component | Time | Batch-wall share |
|---|---:|---:|
| resident sparse GPU pipeline | `47,941.566 ms` | `63.781%` |
| host record-to-hand fold | `15,760.171 ms` | `20.967%` |
| five selector reverse passes per responding seat | `6,138.916 ms` | `8.167%` |
| affected-term discovery and preparation | `4,613.684 ms` | `6.138%` |
| device-to-host transfer | `301.009 ms` | `0.400%` |
| factor preparation | `132.049 ms` | `0.176%` |
| GPU product generation | `82.576 ms` | `0.110%` |
| factor upload | `42.379 ms` | `0.056%` |
| residual | `153.425 ms` | `0.204%` |

The result is consistent with the resident sparse work, rather than launch or
transfer overhead, setting the main cost. It does not prove a particular GPU
occupancy, FP64-throughput, or bandwidth mechanism because no hardware
occupancy or roofline counters were preregistered. Those mechanisms remain to
be separated before a kernel or hardware conclusion.

## The overlay is already active

ADR-0158's terminal-numerator overlay is not an unused follow-up lever in this
path. Both scalar and batched affine implementations compare source and
endpoint target-omitted path factors, contract only changed terminals, overlay
their endpoint numerators on the immutable source tuple, and replay the reverse
tree.

A label-free structural read of ADR-0206's retained regret-vertex coefficient
rows confirms that this optimization is already doing substantial work:
1,920 of 34,740 possible opponent terminal rows are recontracted (`5.527%`),
while `94.473%` are reused. The remaining cost is the exact contraction and
fold for those genuinely affected rows. Re-registering the same overlay under
a new name would duplicate accepted machinery rather than test a new lever.

A source-delta factor can replace endpoint-minus-source algebra exactly, but
with the current tensor-train representation it still requires the same
terminal automaton ranks and per-target-hand output for every affected row.
The present result therefore supplies no basis for predicting a `3x` to `10x`
gain from that rewrite. Any such work-reduction proposal must first name and
count the sparse features or terminal rows it eliminates.

## Complete 15-second ledger

| Retained context | Batched Tier B | Complete ledger | Headroom | Full six fits |
|---|---:|---:|---:|:---:|
| panel 1 balanced | `3,611.6 ms` | `13,415.0 ms` | `+1,585.0 ms` | yes |
| panel 1 blocker-heavy | `3,531.3 ms` | `12,620.8 ms` | `+2,379.2 ms` | yes |
| panel 2 balanced | `4,979.5 ms` | `18,207.8 ms` | `-3,207.8 ms` | no |
| panel 2 blocker-heavy | `4,646.6 ms` | `17,020.1 ms` | `-2,020.1 ms` | no |
| panel 3 balanced | `4,774.1 ms` | `17,727.9 ms` | `-2,727.9 ms` | no |
| panel 3 blocker-heavy | `3,513.6 ms` | `13,195.3 ms` | `+1,804.7 ms` | yes |

Only three of six contexts fit the full six-block B-to-C ledger. The second
prediction, conditional full-set fit after a material batch speedup, receives
no qualifying premise; the observed unconditional full-set result is three of
six.

## Decision

Accept the batch primitive as an exact generic implementation, but reject
cross-candidate call packing as a selector-capacity optimization. Preserve the
scalar path as the timing baseline; the batched path has not earned live
promotion from a non-robust one-percent effect. K remains bound on the three
slow contexts, so do not open a fresh action-conditioned selector corpus yet.

Do not schedule ADR-0158's overlay again: it is already responsible for a
`94.473%` terminal-row reuse rate here. The next numerical differential should
move the record-to-hand fold onto the device for both the warm step and Tier B,
recording host milliseconds removed and device milliseconds added separately
under ADR-0179. It directly attacks `20.967%` of measured Tier-B batch time and
ADR-0198's independent `30.562%` of warm-step time. Reprofile after that
differential. If the resident sparse pipeline still controls K, distinguish
arithmetic from memory/sparse pressure before rewriting its kernel.

Coefficient caching across beliefs remains only a fallback hypothesis. Fixed-
belief affine exactness does not establish slow variation under belief drift;
any cache must be preregistered with structural identity, a numerical staleness
teacher, and fail-closed exact recertification.

This result makes no strategy-quality, transfer, deployment, composition,
population, hardware, occupancy, or broad opportunity-distribution claim.
