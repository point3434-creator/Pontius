# ADR-0170: Fresh-union v1 is rejected by an overstrict warm digest gate

- Status: rejected result
- Date: 2026-08-21
- Implements: ADR-0169
- Clean preregistration commit: `1d0ef0a`
- Failed result: `experiments/results/h32-fresh-union-value-v1.json`
- Failed result SHA-256: `675c1eee9ab70d4390135e0cf82402382188a1c943b24be3827091df57226fe0`

## Formal result

Twenty-two of twenty-three gates passed. The sole failure was exact
`warm_start_identity` on both targets. Therefore the v1 artifact is rejected
and its union and singleton outcomes remain diagnostics rather than accepted
holdout evidence.

Every source checkpoint, target belief, blueprint, union key, immutable anchor,
deadline, fail-closed selector, emission, post-ledger ineligibility, finite,
runtime, memory, count, and broad timing gate passed. Both hard ledgers fit:
`13,640.75 ms` and `13,793.80 ms`, including the frozen one-second emission
reserve. Peak GPU-pool total was `8,214,049,792` bytes and physical free memory
did not fall below `7,032,799,232` bytes.

## Cause

ADR-0169 mistakenly required byte-identical policies immediately after the
regret-mass warm start. ADR-0147 had already established that this is stricter
than the solver contract: encoding Float64 probabilities as regret mass and
normalizing them back can change final bits without a meaningful policy
change. ADR-0148 froze the accepted replacement gates at `1e-12` maximum
probability error and `1e-13` mean information-set total variation.

The v1 artifact did not record those distances, so it cannot be repaired by
reinterpretation. This was a preregistration defect and should have been
avoided by inheriting the corrected ADR-0148 control.

## Diagnostic outcomes from the rejected artifact

On panel 1 balanced, all three union candidates completed inside the cutoff.
The full six-atom union reduced raw NashConv by `5.9949e-8`; all six singleton
atoms also completed, their values summed to the union value within numerical
allowance, and the scalar interaction residual was `5.55e-16`. This is additive
rather than a replication of ADR-0168's strong nonadditivity.

On panel 2 blocker-heavy, the full-six and prefix-four unions both stopped at
seat 3's blueprint cap. The prefix-two union was not started because of the
deadline guard. Five singleton atoms completed and acting-seat 1's singleton
stopped at the same cap. The shadow selector retained the blueprint.

Across the rejected run, five unions were attempted, three completed and were
positive, all three were usable, eleven of twelve atoms completed, and the
immutable blueprint was emitted twice. None of these observations is accepted
evidence until an independently instrumented corrected rerun reproduces it.

## Decision

Preserve the failed artifact. Preregister a successor that reruns the complete
ADR-0169 workload and changes only the exact warm-start digest gate to the
already-established numerical probability and mean-TV gates. Keep exact digest
identity as a diagnostic. Do not alter targets, union order, deadline,
certificate semantics, selector, or any outcome-neutral gate.
