# ADR-0152: Preregister aggregation-corrected fresh-panel action-width rerun

## Status

Frozen after ADR-0151 and before repeating any ADR-0150 h32 step or quality
measurement.

## Context

ADR-0151 rejected the first execution because all target work completed but
the final reporter read `wall_ms` from inner quality mappings rather than
outer profile rows. No artifact was written and no strategic outcome was
inspected or accepted.

The correction is strictly post-work aggregation. It does not change a board,
source, target, order, arm, tree, bet size, warm mass, step, candidate, quality
call, seat order, cap, threshold, selection rule, or claim policy.

## Frozen identities

The corrective config is
`experiments/configs/h32-fresh-panel-action-width-warm-step-v2.json`, SHA-256
`dd59bc7bc2833e9fba2352acf6ab58280734e930534b743e5e5f17f5f94c119a`.
The additive wrapper is
`src/pontius/h32_fresh_panel_action_width_warm_step_audit_v2.py`, SHA-256
`07e527c69708f99063adc1cd099a234460a33f44cc2fa47ddbae5e23c7cc6d68`.
Its direct control is
`tests/test_h32_fresh_panel_action_width_warm_step_audit_v2.py`, SHA-256
`d017084bdc7dc47d4030e98292bcf36a2237f06f29c58f9e02b7c479c5e52e32`.
The corrected result target is
`experiments/results/h32-fresh-panel-action-width-warm-step-v2.json`.

The wrapper pins and reparses ADR-0150's config, SHA-256
`f677e75be8fc2fc3680667799031ad455bf6c81d7a0253ecb3cd9b2e42c14372`,
and reuses its unchanged implementation, SHA-256
`77ee4b7c72e45ff2abfb3c59b75347d8b9ca5cd280cff8e79acf875cdacd557d`.
It also pins ADR-0151, SHA-256
`73cc6feaff2de1b7ea2728d6eaaf1605dfd8d4e6fb318022cfa6696f09895deb`.

## Corrected mechanism

Run ADR-0150 unchanged. At its frozen terminal `KeyError: 'wall_ms'`, capture
the completed local result rows before stack unwinding. Require that exact
error to reproduce; any other exception or unexpected success rejects the
corrective mechanism.

Then assemble:

- outer profile rows for profile count, wall-time ceilings, and quality-phase
  GPU-pool maxima; and
- inner quality mappings for vector-sum exactness, zero-sum residuals, and
  finiteness.

Recompute every ADR-0150 gate with the same thresholds. Include outer profile
GPU-pool maxima in the already frozen 12 GB resource gate. This inclusion
repairs an omission in the failed aggregate expression and strengthens the
existing resource check; it does not change the threshold or strategic
outcome semantics.

## Frozen gates and interpretation

All ADR-0150 gates, decision branches, limitations, and null top-level
strategy-quality claim remain binding. The corrective wrapper additionally
passes only if:

1. ADR-0150's config and implementation and ADR-0151 reproduce exactly;
2. the frozen `KeyError: 'wall_ms'` occurs after the repeated workload;
3. the captured state contains all 12 targets, 24 arms, 24 steps, and 36
   complete profile rows; and
4. the corrected aggregation produces a complete finite JSON artifact.

There remains no gate on strategic direction, arm winner, NashConv reduction,
selection, abstention, added-bet use, or cost ratio. No apparent outcome can
alter the workload or top-level null claim.

## Pre-freeze controls

Two direct controls pass. They reparse ADR-0150, retain all 12 targets and one
step per arm, pin the post-work-only scope, and reject scope, outcome-policy,
or frozen-source mutations. No h32 strategy work was performed.
