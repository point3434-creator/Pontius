# ADR-0209: Preregister the top-level source-pass correction for the Tier-B batch

- Status: accepted schema-only correction preregistration before h32 work
- Date: 2026-08-21
- Corrects: ADR-0207 after ADR-0208
- Config: `experiments/configs/h32-tier-b-opponent-batch-v2.json`
- Config SHA-256: `983c6b72ba3860209a20e7204428ee195c28877069628ee0ebc9190fdf23ce0f`
- Runner: `src/pontius/h32_tier_b_opponent_batch_differential_v2.py`
- Runner SHA-256: `de7ae739f7187d3834d7e7972c7be2754d24052653c90a65b7211e6620ffd734`
- Control: `tests/test_h32_tier_b_opponent_batch_differential_v2.py`
- Control SHA-256: `165e5d6e8471d1b5c4952bcf61a357355bffcc0d49efca4e75459dbdda308f9b`

## Correction

Pin the source-blueprint artifact's complete top-level schema. It contains
`passed` and `gate_results` and does not contain `gates`. Read the source pass
bit only as:

```text
source_parent["passed"]
```

The v2 runner performs that read at the preflight and validity-gate boundaries.
It delegates every target reconstruction, warm step, candidate construction,
own-row read, scalar arm, batched arm, comparison, memory snapshot, and complete
ledger to ADR-0207's frozen implementation. It neither monkeypatches v1 nor
adds a schema alias.

## Frozen inheritance

Hash-pin ADR-0207's config, implementation, control, and decision; ADR-0208;
and the exact source artifact. Preserve unchanged:

- all six retained contexts and six regret-vertex blocks per context;
- 30 scalar versus six batched opponent calls per arm;
- one warmup and the three paired timing repetitions;
- the zero-contraction acting-seat charge;
- ADR-0179 numeric and structural identity gates;
- the `5,184,456,164`-byte prebatch physical-free reserve;
- the 15-second complete B-to-C ledger and one-second emission reserve;
- the no-label, immutable-blueprint, and no-strategy-claim boundary; and
- every report-only prediction and outcome branch.

Write only the versioned v2 result. Reconstruct all state from scratch from a
clean commit. If v2 fails before or during measurement, reject it; do not reuse
v1 process state or reinterpret partial timings.
