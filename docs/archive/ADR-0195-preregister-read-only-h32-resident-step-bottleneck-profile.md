# ADR-0195: Preregister a read-only h32 resident-step bottleneck profile

- Status: accepted preregistration before any replay step
- Date: 2026-08-21
- Config: `experiments/configs/h32-resident-step-bottleneck-profile-v1.json`
- Config SHA-256: `463f6fadb5f0a6039119da149d1d7f6a040a2563233790c4a9863eab72732fcd`
- Runner: `src/pontius/h32_resident_step_bottleneck_profile.py`
- Runner SHA-256: `c77238e017211df9cbd940c386540f3a10a740437afd87dd4f9bdb5696de8033`
- Control test: `tests/test_h32_resident_step_bottleneck_profile.py`
- Control-test SHA-256: `7e7d88b1a7d739ac3691725de0c481073efae9f8f81929b9650603fa02b1a9b5`

## Question

ADR-0194 shows that the resident warm step consumes `6.98` to `10.94`
seconds of the 15-second street while candidate construction and the affine
proof together consume less than half a second. Determine which part of the
warm step should receive the next engineering or hardware dollar.

This is compute time inside the bot's decision boundary, not researcher wall
time. The audit does not search for more poker value; it attributes the cost of
the already accepted mechanism.

## Known evidence and replay boundary

The current machine is already an NVIDIA GeForce RTX 5080 with compute
capability 12.0, an AMD Ryzen 9 9900X3D, and 64 GB of host memory. The retained
128-step deep-horizon trace reports a median resident step of `7.76 s`, of
which the previously serialized resident GPU-pipeline counter explains about
`62.5%`. Roughly `35%` of the step remains aggregated inside terminal work;
the retained artifact does not separate product generation, device-to-host
transfer, and host hand folding.

Replay only the already exposed fastest and slowest ADR-0194 timing targets:

1. panel-1 blocker-heavy seat-4 shift; and
2. panel-2 balanced seat-4 shift.

Their belief and descriptor hashes are copied byte-for-byte from ADR-0193.
Selection uses disclosed timing only. No fresh belief, withheld candidate,
certificate label, NashConv label, or strategy-quality evaluation is allowed.

## Frozen measurement

For each target, compile the same preloaded shared response context used by the
live street path. Then run three exact restarts. Every restart creates a new
resident DCFR solver from the same average-64 blueprint and warm regret mass,
releases only free CuPy-pool blocks, synchronizes the device, and times exactly
one complete step.

Record all six traversers and partition each step into:

- device product generation plus the resident GPU pipeline;
- factor upload plus device-to-host transfer;
- host record-to-hand folding;
- probability compilation, own reach and averaging, factor preparation,
  reverse adjoint, regret application, discount, and unattributed residual.

The partition retains both CPU wall timers and CUDA event timers. Require its
absolute residual to remain at most `15%` of complete step wall time. Policy
digests are diagnostic only. Repeated GPU policies gate numerically at
ADR-0179's `1e-12` maximum probability error and `1e-13` mean information-set
TV ceilings.

## Identification table

Classify by the largest pooled time bucket, with lexicographic tie-breaking.
Classification is reported, not gated.

| Largest bucket | Interpretation | Authorized next screen |
|---|---|---|
| Device GPU | Current kernels dominate | Profile arithmetic versus bandwidth, then benchmark appropriate GPU hardware or kernels |
| Host hand fold | Downloaded record aggregation dominates | Build a device-resident record-to-hand fold before considering a CPU purchase |
| Transfer | PCIe movement dominates | Reduce returned records or fold on device |
| Other host/residual | Current counters are too coarse or host orchestration dominates | Add finer attribution; do not infer a hardware purchase |

Also report serial Amdahl counterfactuals for 2x and 4x device-only speed, 2x
host-fold speed, and 2x all non-device work. These are ceilings under an
explicit serial model, not vendor benchmarks or purchase claims.

## Outcome-neutral validity gates

Require two targets, six restart steps, 36 traverser rows, clean Git state,
parent/result identity, source checkpoint and target identity, numerical warm
start and restart identity, finite complete telemetry, every step at most
`15,000 ms`, a 12 GB CuPy-pool ceiling, at least 1 GB physical GPU memory free,
and at most 600 seconds total audit time.

Do not gate on the dominant bucket, any stage share, estimated speedup, GPU
utilization, or whether a hardware purchase appears attractive. A valid audit
may identify any branch in the table.

## Decision and evidence limit

If every validity gate passes, accept the stage attribution and use only its
dominant-bucket branch to design the next engineering screen. If a gate fails,
reject the attribution and do not use a partial timing row to justify hardware.

This audit cannot establish a latency distribution, FP64-compute versus memory
bandwidth within a CUDA kernel, performance on another machine, deployment
readiness, opponent performance, or strategy quality. It preserves the
immutable blueprint, frozen live rule, and no-composition boundary without
running a certificate or producing an action.
