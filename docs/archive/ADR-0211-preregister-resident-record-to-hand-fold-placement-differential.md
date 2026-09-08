# ADR-0211: Preregister the resident record-to-hand fold placement differential

- Status: accepted engineering preregistration before any h32 placement measurement
- Date: 2026-08-21
- Depends on: ADR-0179, ADR-0198, ADR-0209, and ADR-0210
- Config: `experiments/configs/h32-resident-record-to-hand-fold-v1.json`
- Config SHA-256: `f31807a05d8d7b632b5240b4af71d717e3e8e6ecdf09ad73f98cd61c12f7aee6`
- Audit: `src/pontius/h32_resident_record_to_hand_fold_differential.py`
- Audit SHA-256: `26e17b0d78506d004e3d19d6c1958fa3bf37d694a5725a6be36fc9df2c63df0a`
- Audit control: `tests/test_h32_resident_record_to_hand_fold_differential.py`
- Audit-control SHA-256: `03be212ab71df346adbde99e9915f6f4b06f6ee1a42e824cad46c5068e04100a`
- Fold primitive: `src/pontius/resident_record_to_hand_fold.py`
- Fold-primitive SHA-256: `6cf7428ad2c8d41a3495eab53a9ba245e9e1c30db681b8f3bd14ac642c357969`
- Reduced control: `tests/test_device_fold_resident_paths.py`
- Reduced-control SHA-256: `be4d8b3e20b89776e35c067be6cc4a737d5b1af07d1687a43865deef762d5434`

## Question

ADR-0198 attributes `30.562%` of the complete resident warm-step wall to the
host record-to-hand fold. ADR-0210 independently attributes `20.967%` of the
batched Tier-B wall to the same operation, while also showing that the resident
sparse GPU pipeline remains the larger Tier-B component at `63.781%`.

Does grouping per-record accumulators into target-hand vectors on the GPU
materially reduce complete warm-step and Tier-B wall time under the 15-second
street ledger? Does removing the inter-call host fold barrier make six-way
Tier-B batching useful, or does the ADR-0210 batching null survive the
placement intervention?

This is a label-free implementation differential. It is not a strategy test,
an occupancy study, or a hardware comparison.

## Frozen intervention

Use all six retained ADR-0186 contexts and the same six regret-vertex
public-node blocks reconstructed by the corrected ADR-0209 path. No strategy
label is loaded or joined.

The additive placement pipeline preserves the accepted resident product
generation, width-limited sparse contractions, terminal overlay, and reverse
tree. It changes only the last reduction boundary:

- `host_numpy` downloads the per-record numerator and reach arrays, validates
  and clamps reaches, and folds them with the accepted NumPy operation;
- `gpu_cupy` validates and clamps the same per-record reaches on-device,
  atomically groups numerator and reach values into per-hand Float64 vectors,
  and downloads only those vectors plus per-term reach diagnostics.

The new host arm is an intervention control through the same additive
dispatcher, not a silently rewritten baseline. The reduced tests require both
placements to match the accepted resident vectors, one complete DCFR warm
step, independent affine rows, and batched affine rows. The h32 warm arm is
also compared directly with the accepted ADR-0209 host-step state. Every Tier-B
cell is compared with an untimed accepted scalar teacher.

## Two customers and the four-cell Tier-B test

Measure one complete six-traverser warm step under:

```text
host_fold, device_fold
device_fold, host_fold
host_fold, device_fold
```

Warm each arm once before the three paired repetitions. Construct a fresh
solver from the identical blueprint and warm mass for every sample, and time
only the complete step.

For Tier B, warm and then measure these four cells in the frozen three-order
schedule from the config:

```text
host_scalar  host_batch  device_scalar  device_batch
```

Scalar cells make 30 opponent-conditioned calls. Batch cells make six calls,
one per responding seat, and produce the same 30 semantic rows. Acting-seat
rows remain the separately timed exact zero-contraction rows from ADR-0209.
This 2x2 separates invocation topology from fold placement. Mere serial
deferral of unchanged host folds is not treated as a distinct arm because it
conserves the charged work and cannot establish overlap by itself.

Report host fold milliseconds removed, device fold milliseconds added,
residual host finalization, device-to-host milliseconds and bytes, sparse GPU
pipeline time, width-limited pass count, and a feature-width fill proxy. The
proxy is not called occupancy.

## Numerical and structural identity

ADR-0179 controls the reassociated device reduction. Exact output digests are
diagnostics only. Require:

- complete warm-step regret and strategy-sum errors at most `1e-12`;
- current-policy maximum probability error at most `1e-12` and mean
  information-set total variation at most `1e-13`;
- every affine coefficient and reconstructed composite within `2e-11`;
- exact regret-table, strategy-sum, iteration, candidate, selector-switch,
  affected-terminal, and reuse structure; and
- the device placement to transfer fewer output bytes than the host placement
  separately for the warm step, scalar Tier B, and batched Tier B.

The host path must report positive host-fold time and zero device-fold time.
The device path must report positive device-fold and residual host-finalize
time and zero host-fold time. These are accounting gates, not performance
gates.

## Timing, memory, and profiler separation

Release only unreferenced CuPy pool blocks and synchronize at every arm
boundary. Retain every sample and use medians for decisions. Speed is not a
validity gate.

Stop before placement work if physical-free memory is below
`5,184,456,164` bytes. During the audit, CuPy-pool allocation must remain at
most `12,000,000,000` bytes and physical-free memory at least
`1,000,000,000` bytes. The full audit ceiling is `2,400 s`.

Nsight Compute 2026.2.1 is installed. The paired process may query only its
non-gating availability and version; it must not collect hardware counters.
Counter collection serializes or perturbs launches and would contaminate the
paired times. If the result still points to the sparse pipeline, run a later
single-call Nsight artifact with no validity or timing role here.

## Global choice and complete street ledger

After every target is complete, choose exactly one device Tier-B topology for
all contexts: the lower pooled wall-time median of `device_scalar` and
`device_batch`, with scalar winning an exact tie. This choice uses no strategy
label and cannot vary by target.

For every retained context charge exactly once:

1. the median device-fold complete warm step;
2. construction of all six endpoints;
3. all six exact acting-seat rows;
4. the globally selected complete device Tier-B cell;
5. ranking plus one winner affine envelope; and
6. the frozen one-second emission reserve.

Report signed headroom and whether all six blocks fit `15,000 ms`. Also report
a linear current-library K estimate obtained by scaling only the observed
six-block variable bill. That estimate is explicitly diagnostic: it is not a
prefix measurement and cannot support a widened-library capacity claim.
Emit only the immutable blueprint.

## Frozen predictions and decision branches

The ideal zero-cost removal ceiling is bounded by the measured host-fold
shares; the device fold itself is not free. Register the restrained prediction
that device placement improves both customers, but do not predict a Tier-B
miracle while its sparse pipeline remains dominant.

H3, the host-fold barrier account of ADR-0210's batching null, is resurrected
only if the median device batching speedup reaches `1.10x` and its
device-versus-host batching interaction reaches `1.08x`. Otherwise H3 is dead
by intervention and batching remains a null optimization at this geometry.

An implementation customer earns promotion only when its pooled speedup is at
least `1.05x` and no retained target regresses by more than `2%`. These are
preregistered decision thresholds, not validity gates:

- if provenance, identity, accounting, or memory fails, reject the
  differential and retain the accepted host paths;
- if both customers clear promotion, accept the device fold for both;
- if only one clears, promote it only at that call site;
- otherwise retain the host fold and move directly to the separate sparse
  hardware profile; and
- regardless of speed, open no fresh action-conditioned label corpus until the
  complete street ledger has been repriced and sealed.

No branch authorizes a strategy-quality, transfer, deployment, population,
composition, GPU-occupancy, roofline, or hardware-purchase claim.
