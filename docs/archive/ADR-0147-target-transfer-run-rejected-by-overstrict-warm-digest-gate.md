# ADR-0147: Target-transfer run is rejected by an overstrict warm digest gate

## Status

ADR-0146 executed from clean preregistration commit
`ec322805962e91732d70c3bc570d49ef96f837eb`, but the artifact is not accepted.
Twenty-three of twenty-four gates passed; `warm_identity` failed on the frozen
exact-policy-digest requirement.

## Evidence

The 958,121-byte failed artifact is
`experiments/results/h32-fresh-panel-target-transfer-v1.json`, SHA-256
`9d00b82bab234e2785b3add4468ee2190d5c71e3dbb547ec7447436d3617dd37`.
It completed in `1050.6319 s` from strict clean Git state.  All twelve targets,
24 search steps, 12 blueprint profiles, and 72 candidate profiles completed.
All source, target, checkpoint, restore, finite, zero-sum, cap, certificate,
count, and resource gates passed.

## Failure cause

The preregistration required the policy digest immediately after regret-mass
warm start to equal the source policy digest.  That is stricter than the
accepted warm-start contract used by the h32 lineage.  Encoding probabilities
as Float64 regret mass and normalizing them back can change last-bit policy
values without changing the intended behavior.  Prior audits therefore gate
maximum probability error at `1e-12` and mean total variation at `1e-13`.

This is a methodology defect, not evidence that target transfer or resident
DCFR is inexact.  The v1 artifact did not record the numerical warm-start
distance, so the failed gate cannot be repaired by reinterpretation.

## Diagnostic outcomes

The failed artifact observed one non-blueprint selection among twelve targets:
panel 2 balanced under the local blocker shift selected `search_current2` with
normalized NashConv reduction approximately `1.4533e-4`.  The other eleven
targets abstained to their blueprints.  These are diagnostics from a rejected
artifact and are not accepted transfer evidence.

## Decision

Preserve the failed artifact.  Preregister a successor that changes only the
warm-start identity measurement to the established numerical tolerances,
records both errors for every target, and reruns the complete frozen matrix.
Do not alter candidates, target order, acceptance semantics, or any outcome
gate.
