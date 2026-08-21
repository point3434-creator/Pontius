# ADR-0188: Selector-stable affine v1 is rejected by a forbidden warm digest gate

- Status: rejected result
- Date: 2026-08-21
- Implements: ADR-0187
- Clean preregistration commit: `f0509ea79cbb0208107d0a9e81e56a76b6ee3001`
- Failed result: `experiments/results/h32-selector-stable-affine-certificate-v1.json`
- Failed result SHA-256: `19daba7a043bc2cb7cc12935847eabfe3af88bfeccf2cb47e1260f124cdf8637`

## Formal result

Thirty of thirty-one outcome-neutral gates passed. The sole failure was
`numerical_warm_start_identity`, so the v1 artifact is rejected and none of
its affine selections, value, or street-fit observations is accepted evidence.

Every immutable source, target, checkpoint, blueprint, public block, and
regret-vertex direction identity passed. All 36 fixed direct witnesses were
strictly inside their selector-stable intervals with zero response flips. All
35 selected scales completed the old exact verifier with zero response flips.
The maximum utility, best-response, and deviation-gain errors were respectively
`1.2213e-15`, `1.3878e-15`, and `4.9960e-16`.

## Cause

ADR-0187 correctly froze the established numerical warm-start ceilings at
`1e-12` maximum action-probability error and `1e-13` mean information-set total
variation, but its implementation mistakenly conjoined those gates with exact
cross-run equality of the post-step policy SHA-256. All six digests differed.
The largest probability error was only `2.220446049250313e-16`, and the largest
mean total variation was `3.4368857247098436e-17`.

This exact digest requirement violates ADR-0179: the policy was independently
re-derived through GPU sparse reductions, not restored and re-exported as a
literal serialized object, and deterministic future execution was not the
subject of the experiment. ADR-0187 even depended on ADR-0179, so this is a
preregistration and review failure rather than a newly discovered numerical
property. The recorded distances cannot rescue the run because the forbidden
digest was nevertheless a frozen pass gate.

## Diagnostics from the rejected artifact

The affine envelope selected 35 of 36 public blocks and captured
`5.9921299009e-6` positive certified value, or `48.8025%` of ADR-0186's frozen
three-family bounded-oracle value. The one abstention was acting seat 1 at
`p0:bet` on panel 2 balanced, where the affine objective was non-improving.

All six descriptive seat-0 ledgers fit the 15-second street boundary including
the one-second reserve. They ranged from `9,233.70 ms` to `13,203.70 ms`.
Maximum GPU-pool allocation was `8,214,049,792` bytes, physical-free memory did
not fall below `7,032,799,232` bytes, and the complete off-clock audit took
`230.3400 s`.

These observations are diagnostics only. In particular, v1 does not validate
the affine primitive, authorize a fresh street trial, emit a candidate, or
support a strategy-quality or population claim.

## Decision

Preserve the failed artifact. Preregister a successor that repeats the entire
ADR-0187 workload and changes only the warm-start pass condition: use ADR-0179's
already-frozen numerical probability and mean-TV gates, imported from the
repository evidence protocol, while retaining exact digests as diagnostics.
Keep every target, direction, proof, direct teacher, ledger, resource gate, and
outcome policy unchanged. Add no gate derived from the favorable v1 outcomes.
