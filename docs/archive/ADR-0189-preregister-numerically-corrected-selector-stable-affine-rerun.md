# ADR-0189: Preregister the numerically corrected selector-stable affine rerun

- Status: accepted successor preregistration
- Date: 2026-08-21
- Corrects: ADR-0187
- Preserves: ADR-0188 failed artifact and all v1 scientific outcomes as diagnostics

## Sole correction

Rerun the complete ADR-0187 six-target differential from its byte-pinned v1
configuration and implementation. Replace only the rejected conjunction of
numerical warm-start equivalence and exact post-step policy-digest equality
with ADR-0179's repository-default numerical contract:

- maximum action-probability error at most `1e-12`; and
- mean information-set total variation at most `1e-13`.

Import those constants from `pontius.evidence_protocol`. Record all exact
digest comparisons as diagnostics and require none of them to pass. The
successor adds no solver step, target, direction, endpoint, certificate,
quality label, timing branch, or candidate emission.

## Frozen rerun scope

Reuse without alteration:

- the six retained ADR-0186 seat-2 targets and source average-64 blueprints;
- one resident warm DCFR step per target;
- the same 36 regret-vertex public blocks and direction identities;
- all 216 selector-stable affine responding-seat rows;
- the half-radius, geometric-halving scale grid, and numerical allowances;
- all 36 fixed direct witnesses and every selected-scale old-verifier teacher;
- the descriptive seat-0 ledger and one-second emission reserve;
- immutable-blueprint emission; and
- every v1 exactness, topology, count, runtime, memory, and fail-closed gate.

The v1 config, implementation, control test, failed result, rejection ADR,
repository evidence protocol, successor implementation, and successor control
test are SHA-bound in
`experiments/configs/h32-selector-stable-affine-certificate-v2.json`.

## Outcome policy

No v1 selected count, scale, value, capture fraction, abstention, selector
radius, street fit, or latency is a successor gate. Decision-signature
reproduction is diagnostic only. The corrected run passes only if both
numerical warm-start gates and every unchanged v1 outcome-neutral gate pass.

If it passes and all retained descriptive seat-0 ledgers fit, ADR-0187's
original decision rule permits a separately preregistered fresh street trial.
It does not itself authorize deployment, certificate composition, candidate
emission, or a strategy-quality or population claim.
