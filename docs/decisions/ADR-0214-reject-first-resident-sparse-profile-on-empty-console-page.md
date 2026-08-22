# ADR-0214: Reject the first resident-sparse profile on an empty console page

- Status: accepted tooling rejection; no counter interpretation
- Date: 2026-08-21
- Depends on: ADR-0213
- Result: `experiments/results/h32-resident-sparse-ncu-profile-v1.json`
- Result SHA-256: `59801f5643b0e8c9bf7efe538a42ddc23c3802f5a4c53bc1f50b3ff2fd3745de`
- Preregistered commit: `710d7f7`

## Result

The clean ADR-0213 invocation reconstructed both frozen resident operators and
completed both direction workloads. Nsight returned code zero, reported no
`ERR_NVGPUCTRPERM`, and each workload emitted finite metadata under a maximum
CuPy pool allocation of `961,623,552` bytes. The run took `12.244916 s`.

Nevertheless, neither invocation emitted a raw CSV header or any kernel row to
the captured console stream. The parser therefore returned `Nsight output
contains no raw CSV header` twice. The frozen kernel-count and NVTX-identity
gates failed, the artifact contains zero profiled kernels, and the result is
rejected.

No counter value is available to classify. The run supports no pressure,
timing, strategy, rewrite, hardware, or purchase claim.

## Cause

The driver selected `--page raw` but left Nsight Compute 2026.2.1's
`--print-summary` option at its documented default of `none`. With that
combination the profiler can collect successfully and remove its temporary
report while printing no per-kernel console page. The workload and permissions
were not the failed gates; the missing console-output request was.

This diagnosis uses the local profiler's `--help` output after the failed run.
It does not use or interpret an h32 counter value.

## Correction boundary

Preserve this result and every ADR-0213 source byte. A versioned correction may
add exactly `--print-summary per-kernel`, require a nonempty stdout payload,
and make core-metric presence non-vacuous. Before another h32 collection, pin
the rejected result and this decision, prove the corrected parser on a
non-h32 canary or synthetic wide CSV, and commit the correction from a clean
tree.

All ADR-0213 workload, NVTX, metric, classifier, memory, duration, and claim
boundaries otherwise remain unchanged.
