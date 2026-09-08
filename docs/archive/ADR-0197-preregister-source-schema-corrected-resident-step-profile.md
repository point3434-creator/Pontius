# ADR-0197: Preregister the source-schema-corrected resident-step profile

- Status: accepted correction preregistration before any replay timing
- Date: 2026-08-21
- Corrects: ADR-0195 after ADR-0196
- Config: `experiments/configs/h32-resident-step-bottleneck-profile-v2.json`
- Config SHA-256: `cd67b4a191eff0f629c94e922650c7e1cce4618a6a86daee77e31d50f4af850c`
- Runner: `src/pontius/h32_resident_step_bottleneck_profile_v2.py`
- Runner SHA-256: `9ecfd18a607080522aba0323a313ae4c3cb0400aae9aba0da307e2cd0a0765db`
- Control test: `tests/test_h32_resident_step_bottleneck_profile_v2.py`
- Control-test SHA-256: `d9208f5dfa8ff8ddbfc4c673cf61f85c4e531eccf2701cb0c570e74f90d457e2`

## Correction

ADR-0196 rejected v1 before `_run_target` because its source-parent validity
check asked for a nonexistent nested `gates.passed`. Add one in-memory view for
the exact retained source-blueprint artifact:

```text
gates.passed := top-level passed
```

Do not modify or rewrite the source artifact. The alias is permitted only when
the parsed object has status
`frozen_h32_fresh_panel_source_blueprints_executed`, contains `source_rows`,
contains a top-level Boolean `passed`, and does not already contain `gates`.
Every other JSON object is returned unchanged.

The additive wrapper pins:

- ADR-0195's config at
  `463f6fadb5f0a6039119da149d1d7f6a040a2563233790c4a9863eab72732fcd`;
- its runner at
  `c77238e017211df9cbd940c386540f3a10a740437afd87dd4f9bdb5696de8033`;
- its control test at
  `7e7d88b1a7d739ac3691725de0c481073efae9f8f81929b9650603fa02b1a9b5`;
- ADR-0195 at
  `929c89cf1e82e9cfdc6b15d00c43ede009d6d31d94d9ab563e9e5871de3197f9`;
  and
- ADR-0196 at
  `f54ed5dc36fe147e0603771ec0f14bef494327b9041f75ae1f78a4323da8690b`.

## Scientific identity

Reuse ADR-0195 byte-for-byte for its two disclosed timing-extreme targets,
three exact restarts per target, preloaded response context, solver state,
warm mass, device synchronization, timing boundary, stage buckets, Amdahl
counterfactuals, numerical tolerances, validity gates, hardware identity, and
classification table. The wrapper changes no target, loop count, measured
field, threshold, result branch, or strategy boundary.

Classification remains report-only. No strategy-quality label, affine proof,
fresh target, or candidate action may run.

## Evidence boundary and decision

All six replay timings remain unobserved at this freeze. Four focused controls
show that the alias adds only the expected nested view, refuses the wrong
artifact or a preexisting nested schema, ignores all other JSON, and preserves
every v1 scientific field.

Run once from the clean successor commit. If every inherited validity gate
passes, accept the attribution and follow its preregistered dominant-bucket
branch. Otherwise reject v2; do not make another unrecorded correction or use
partial timings to support a hardware choice.
