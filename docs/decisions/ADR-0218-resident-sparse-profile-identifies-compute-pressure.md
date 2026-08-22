# ADR-0218: The resident-sparse profile identifies compute pressure

- Status: accepted diagnostic result
- Date: 2026-08-21
- Depends on: ADR-0217
- Result: `experiments/results/h32-resident-sparse-ncu-profile-v3.json`
- Result SHA-256: `cf0f734f2c975a04dd7b43e6476e5ab885a882ee8d3bb6323e598dc76dfaf388`
- Preregistered commit: `989ce89`

## Result

The final target-corrected profile passed every frozen gate. It retained seven
NVTX-isolated kernels in each traversal direction, all required core metrics,
the exact width-384 workload and source digest, finite outputs, and a maximum
CuPy pool allocation of `961,623,552` bytes. Total profiler process wall was
`33.699913 s`.

Both directions independently satisfy the preregistered `compute_pressure`
rule:

| Direction | Dominant duration share | SM throughput | Peak memory throughput | Peak level | Achieved occupancy | Waves/SM |
| --- | ---: | ---: | ---: | --- | ---: | ---: |
| right-to-left | 95.838% | 81.095% | 40.226% | L2 | 95.676% | 262.002 |
| left-to-right | 95.740% | 81.209% | 39.593% | L2 | 95.645% | 265.726 |

In each direction, two `cusparse::csrmm_alg1_kernel` launches form the minimum
prefix covering at least `90%` of kernel duration. SM throughput is above the
frozen `60%` threshold and more than `1.25x` the largest memory-throughput
signal. High achieved occupancy and hundreds of waves per multiprocessor rule
out the frozen launch-or-occupancy signature at this width.

## Interpretation

At the profiled maximum-width geometry, the accepted two-SpMM sparse pass is
device-compute pressured rather than launch-starved or memory-pressure
dominated. This supplies direct mechanism evidence for ADR-0210 and ADR-0212's
batching null: the individual width-384 calls already keep the device busy, so
packing six calls cannot create a missing occupancy or launch-amortization
win.

This is a diagnostic inference from counter patterns, not a causal ordinary-
wall speedup result. Nsight kernel replay stretched the workload's diagnostic
CUDA-event median to about `10.516 s`; that number has no place in the
15-second street ledger. ADR-0212 remains the sole accepted ledger.

## Decision

Retire launch-amortization, six-call batching, and occupancy tuning as current
optimization theses for the width-384 resident sparse pass. Preserve the exact
batch implementation as a semantic primitive, but do not schedule it as a
performance lever.

Do not open a speculative custom-SpMM or reduced-precision rewrite. The
dominant work is already inside cuSPARSE, achieved occupancy is high, and the
frozen Float64 numerical contract leaves no obvious cheap bounded change whose
expected value precedes the planned scientific spend. Any future kernel change
requires a separately preregistered ADR-0179 identity and ordinary paired-wall
differential against the accepted device-fold path.

Proceed to preregister the fresh action-conditioned widened corpus using the
sealed ADR-0212 wall ledger. Selection remains unbound only for the retained
six-block library; the widened corpus is where the affine composite and honest
capacity-priced K receive their first deployment-shaped test.

No strategy is populated. This result makes no strategy-quality, transfer,
deployment, population, roofline, hardware-comparison, or GPU-purchase claim.
