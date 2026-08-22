# ADR-0213: Preregister the isolated resident-sparse Nsight profile

- Status: accepted diagnostic preregistration before any h32 counter collection
- Date: 2026-08-21
- Depends on: ADR-0179, ADR-0209, ADR-0210, ADR-0211, and ADR-0212
- Config: `experiments/configs/h32-resident-sparse-ncu-profile-v1.json`
- Config SHA-256: `b7e84e772ac80a40c89d1b24ab7af9aa4c144ae9f9dc3f21a864be3adbd51cc6`
- Profile driver: `src/pontius/h32_resident_sparse_ncu_profile.py`
- Profile-driver SHA-256: `18d3e21e6dd2fb05da979bb4f6c8357d4fcf41e7dc4acdfac1423d94f8ad7fed`
- Isolated workload: `src/pontius/h32_resident_sparse_ncu_workload.py`
- Isolated-workload SHA-256: `b3798ecd89287cbe4daf940b8268ecec935984ce92c70d157ec0ebb9d7513473`
- Audit control: `tests/test_h32_resident_sparse_ncu_profile.py`
- Audit-control SHA-256: `46f9763376fe5a2bcb1e62089c616c21f12707ac313b38a773632e5108d5f47b`

## Question

ADR-0212 moved the record-to-hand fold onto the GPU and reduced the complete
warm-step median by `1.446699x`. It also reduced the globally selected Tier-B
cell by `1.264880x`, while showing that the resident sparse pipeline now
accounts for `97.987%` of warm-step wall and `81.141%` of device-batch Tier-B
wall. Six-way batching remained neutral after the placement intervention.

What resource-pressure class describes the actual maximum-width resident
sparse contraction: memory pressure, compute pressure, launch or occupancy
pressure, or a mixed unresolved case? The answer may nominate a later
engineering differential. It cannot authorize one by itself.

This is a label-free hardware-counter profile. It is not an ordinary timing
test, a strategy experiment, a GPU comparison, or a purchase recommendation.

## Evidence boundary

Nsight Compute 2026.2.1 was already installed. Counter access initially failed
with `ERR_NVGPUCTRPERM`. After the user enabled NVIDIA performance counters, a
small non-h32 canary returned real launch and occupancy metrics. A second
canary established the push/pop NVTX filter syntax: a range named `R` is
selected by the expression `R]`.

Those permission and syntax canaries are tooling reconnaissance only. No h32
resident sparse operator has been profiled. Commit this ADR, its config,
driver, workload, and controls in a clean tree before the first h32 counter
collection.

## Frozen workload

Use only the retained `panel_2/balanced/local_blocker_seat2_x2` source with
belief digest
`0662b2cf2436cbc6dcc5669fe75a2c15f03e652fb40a6903703a10dd14cfa289`.
Reconstruct the accepted h32 sparse topology and compile the actual resident
CuPy CSR operators. Do not load or join a strategy label.

Profile both accepted directions separately:

1. `right_to_left`; and
2. `left_to_right`.

For each direction, create a deterministic nonzero Float64 dense feature
matrix at the frozen maximum feature width of `384`. Warm the operator twice
outside the observed range. Inside the direction-specific NVTX range, execute
exactly the two accepted sparse products:

```text
incidence = source_matrix @ features
compatible = query_matrix @ incidence
```

Synchronize before leaving the range. The dense values are synthetic, while
the matrix shapes, nonzero structure, traversal direction, and feature width
are actual. Record output finiteness, a checksum, shapes, nonzero counts,
numeric bytes, diagnostic CUDA-event time, and CuPy-pool allocation.

## Frozen profiler protocol

Invoke Nsight Compute once per direction with application-only targeting,
kernel replay, the `basic` metric set, rules disabled, raw wide CSV output,
and only the exact push/pop NVTX range. Retain the selected metric subset and
a digest of the raw CSV, not a mutable `.ncu-rep` file.

Kernel replay serializes and may repeat kernels. Therefore its process wall
and counter-derived kernel durations are not comparable to ADR-0212's ordinary
wall-time ledger. Counter values have no validity role beyond being present
and finite.

Require two directions, at least two profiled kernels per direction, the
correct NVTX range and width, a finite workload, all frozen core metrics, a
CuPy pool no larger than `12,000,000,000` bytes, and no more than `1,800 s`
total profile wall. Both pinned parents must have passed, every source hash
must match, Nsight must exist, counter permission must remain available, and
the Git tree must be clean.

## Frozen diagnostic classifier

Within each direction, sort kernels by counter-reported duration and retain
the minimum prefix covering at least `90%` of profiled kernel duration.
Duration-weight the retained kernels' SM throughput, DRAM throughput, L2
throughput, L1/texture throughput, achieved occupancy, and waves per
multiprocessor. Define memory pressure as the largest of the three memory
throughputs.

Classify the direction under these fixed rules:

- `memory_pressure` when memory is at least `60%` and at least `1.25x` SM;
- `compute_pressure` when SM is at least `60%` and at least `1.25x` memory;
- `launch_or_occupancy_pressure` when both are below `50%` and either achieved
  occupancy is below `40%` or waves per multiprocessor are below `1`; or
- `mixed_or_unresolved` otherwise.

If both directions agree, report that shared diagnostic. Otherwise report a
direction-mixed result. These thresholds are descriptive screens, not proof
that a named bottleneck causes ordinary wall time.

## Outcome policy

A passing profile may prioritize one separately preregistered implementation
differential. It may not rewrite a kernel, change the street ledger, unretire
batching, widen the candidate corpus, or change the solver contract by itself.
Any proposed rewrite must preserve ADR-0179 numerical ceilings and defeat its
accepted baseline in ordinary paired wall time.

The profile populates no strategy and makes no strategy-quality, transfer,
deployment, population, hardware-comparison, roofline, or GPU-purchase claim.
After sealing the result, the next scientific item remains the fresh
action-conditioned widened corpus unless this diagnostic identifies a cheap,
bounded engineering differential whose expected value clearly precedes that
spend.
