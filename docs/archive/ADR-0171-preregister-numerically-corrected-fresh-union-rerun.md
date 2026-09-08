# ADR-0171: Preregister the numerically corrected fresh-union rerun

- Status: accepted successor preregistration
- Date: 2026-08-21
- Corrects: ADR-0169
- Preserves: ADR-0170 failed artifact and all scientific outcomes as diagnostic

## Sole correction

Rerun the complete ADR-0169 two-target experiment from its byte-pinned v1
configuration and implementation. Replace only the rejected exact warm-start
policy-digest gate with the established ADR-0148 numerical contract:

- maximum action-probability error at most `1e-12`; and
- mean information-set total variation at most `1e-13`.

Record exact digest identities as diagnostics. Do not require them to pass.
The instrumentation subclasses the same resident solver, calls the same warm
start, and measures its current strategy immediately afterward. It adds no
step, policy, target, certificate, quality label, or outcome branch.

## Frozen rerun scope

Reuse without alteration:

- both seat-4 target beliefs and source average-64 blueprints;
- one resident DCFR step per target;
- the six lexicographically selected atoms;
- full-six, prefix-four, and prefix-two union order;
- immutable blueprint anchor and ascending seat verifier order;
- the 15,000 ms budget, 1,000 ms emission reserve, and 1,250 ms start guard;
- shadow-selection and immutable blueprint-emission rules;
- all six post-ledger singleton diagnostics; and
- every v1 count, exactness, resource, deadline, and fail-closed gate.

The failed result, v1 config, v1 implementation, v1 control test, rejection ADR,
successor implementation, and successor control test are all SHA-bound in
`experiments/configs/h32-fresh-union-value-v2.json`.

## Outcome policy

No v1 union completion, stop reason, value, interaction signature, selector
decision, timing, or decision-level reproduction is a gate. The successor
records decision-signature identity and maximum common complete-NashConv
difference only as diagnostics.

The corrected run passes only if both numerical warm-start gates and every
unchanged outcome-neutral v1 gate pass. Until then, the ADR-0170 observations
remain rejected diagnostics. Even a pass describes only the two frozen targets,
emits the blueprint, and authorizes neither deployment nor certificate
composition.
