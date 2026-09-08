# ADR-0215: Preregister the corrected resident-sparse console page

- Status: accepted tooling correction before any corrected h32 counter collection
- Date: 2026-08-21
- Depends on: ADR-0213 and ADR-0214
- Config: `experiments/configs/h32-resident-sparse-ncu-profile-v2.json`
- Config SHA-256: `0f0ea45a4529911600979e7bcee3bcb7cc46220bb2aa96babffd6d2e7290d80b`
- Corrected driver: `src/pontius/h32_resident_sparse_ncu_profile_v2.py`
- Corrected-driver SHA-256: `acc6afdba1507d844ae1ee8d8744d2a1f9a7f02c39ba328544b7a04e87426629`
- Corrected control: `tests/test_h32_resident_sparse_ncu_profile_v2.py`
- Corrected-control SHA-256: `75fc257a89460887fd832d48459147f32c8eea9299681ca72b9eecde97e6c0fe`

## Decision

Repeat the rejected ADR-0213 profile with one profiler-output correction:
request `--print-summary per-kernel` explicitly. Preserve the rejected result,
the original driver, and the original workload byte-for-byte.

The v2 config hash-pins the ADR-0213 config, driver, control, rejected result,
and ADR-0214 rejection. The corrected driver and its control are also pinned.
It invokes the exact ADR-0213 workload with the exact rejected v1 config.

## Corrected gates

In addition to every ADR-0213 gate, require nonempty stdout for each direction.
Core-metric presence and metric finiteness now require a nonempty kernel set,
so neither condition can pass vacuously when console output is absent. The
control requires the corrected command to contain the explicit per-kernel
summary request and prevents the v2 driver from overwriting the v1 artifact.

No metric, set, replay mode, target, traversal direction, width, warmup, NVTX
range, sparse product, threshold, memory ceiling, duration ceiling, or outcome
policy changes. No failed v1 process state is reused.

## Claim boundary

This is a versioned tooling repair, not an adaptive scientific rerun. A passing
v2 artifact may report only the frozen ADR-0213 diagnostic pressure class and
may nominate a separately preregistered ordinary-wall differential. It makes
no strategy-quality, transfer, deployment, population, kernel-speedup,
hardware-comparison, roofline, or GPU-purchase claim.
