# ADR-0135: The h32 action-width audit fails its target-descriptor gate

## Status

ADR-0134 executed once from clean commit `5476a3a`.  Nineteen of twenty frozen
mechanism gates passed, but `target_identity` failed on all four rows.  The
artifact is rejected as a strategy-quality result and is not relabeled after
inspection.

## Evidence identity

The 28,801,714-byte artifact is
`experiments/results/h32-action-width-quality-v1.json`, SHA-256
`87de94cf58007eb5b118b86b0ca44c8c9ac78c05280d5f64bcc01b8eb7497669`.
Its configuration SHA-256 is
`1431e57e2fc0e640a16aed0488a7f1070897a17740a33c273b5e1e9b9a44fa60`.
The runner SHA-256 recorded by both config and result is
`a7072bec66e9febe179f1f1e42cd29f2e5c5efa4ef9809935d3f91071494b728`.
Strict Git metadata reports the clean full commit
`5476a3a10fb4f063580a141eb541303731128cd5`.  The run completed normally in
`912.1285 s`; it did not crash, overrun, or require a retry.

The h2 control reproduced exact embedded profile utility, quality error
`3.553e-15`, zero-sum residual `1.645e-15`, all 378 canonical bases, and exact
compact-policy round trips.

## Failed gate localization

Every reconstructed h32 target belief digest exactly equals its frozen
ADR-0113 digest:

| Target | SHA-256 identity |
|---|---:|
| balanced / local blocker | pass |
| balanced / all-seat strength | pass |
| blocker-heavy / local blocker | pass |
| blocker-heavy / all-seat strength | pass |

Hand axes also reproduce exactly.  For every target, the newly constructed
descriptor exactly equals the projection of the parent descriptor onto the
new descriptor's keys.

The runner nevertheless compared the two complete descriptor mappings for
equality.  `_build_target_belief` returns the immutable construction
descriptor: 11 fields for the local-blocker shift and eight for the strength
shift.  ADR-0113 later augmented those same mappings with seven measurement
fields: marginal timing, marginal total variations, source and target
partitions, and their ratio.  An 11-field or eight-field mapping cannot equal
its 18-field or 15-field augmented parent.  The predicate was therefore
structurally false even when its belief digest, axes, and every construction
field matched.

This is a false-negative audit predicate, not evidence that a different target
was solved.  It is still a frozen gate failure.

## Passing diagnostic evidence

All other gates passed: parent and source identity, clean Git state, small
control, target order, arm count, topology and policy width, game-derived
payoff spans, complete-step and deadline bounds, cache construction, 378-basis
identity, compact serialization, planning-before-quality order, exact-quality
bounds, immutable-cap compliance, GPU ceiling, and total wall time.

The wall-clock arms completed five or six one-size steps versus two two-size
steps.  Cold one-size cache construction ranged from `2.910` to `3.926 s`;
scale-canonical two-size construction ranged from `20.661` to `27.150 s`.

| Family | Arm | Persistent bytes | Total / maximum middle rank | Pool total | Headroom below 12 GB |
|---|---|---:|---:|---:|---:|
| balanced | one size | 4.232 GB | 10,590 / 105 | 4.298 GB | 7.702 GB |
| balanced | two size | 4.020 GB | 20,648 / 105 | 4.086 GB | 7.914 GB |
| blocker-heavy | one size | 3.468 GB | 9,966 / 99 | 3.527 GB | 8.473 GB |
| blocker-heavy | two size | 3.295 GB | 19,432 / 99 | 3.353 GB | 8.647 GB |

These repeat the accepted resident-cache geometry under the actual shot-clock
workload.  They are retained as systems diagnostics, not promoted through the
failed aggregate gate.

## Strategy-output disposition

Each arm emitted four unique candidates on every target.  All 32 candidates
were stopped early by an immutable incumbent seat cap; no complete candidate
entered the selector.  Both arms therefore abstained to the embedded blueprint
on all four targets, and the stored selected normalized reduction is zero for
both arms.

That zero-versus-zero output is diagnostic only.  The top-level artifact says
`passed=false`, `decision=reject_action_width_audit_mechanism`, and
`strategy_quality_claim=null`.  No one-size win, two-size loss, equivalence,
or claim about the strategic value of a second size follows from ADR-0135.

## Decision

Preserve the failed artifact unchanged.  Do not weaken or recompute its gate
in place and do not silently rerun ADR-0134.

The cheapest faithful repair is an additive successor that pins this exact
failed artifact and requires its only failed gate to be `target_identity`.
Before that successor runs, freeze an explicit target-identity contract:

1. exact belief digest and hand-axis identity;
2. an exact, shift-specific construction-descriptor field set; and
3. exact equality between that construction descriptor and the corresponding
   projection of ADR-0113's augmented descriptor.

The successor must retain every v1 workload, deadline, candidate, verifier,
resource, and outcome-neutral gate.  It must add a regression control that
passes augmented parents and fails any changed construction field or belief
digest.  Because the v1 outcome is now known, the successor must disclose that
fact and cannot present itself as a pre-outcome discovery.

## Dissent

**Confidence:** very high in the localization because all four belief hashes
and all four projected descriptors match exactly; high that a projection-based
contract tests the intended immutable identity.

**Opposing evidence:** the completed arithmetic could be post-hoc adjudicated
without rerunning.  A single successor rerun is more conservative because it
re-executes every arm and exact verifier under the corrected gate rather than
selectively accepting stored labels.

**Largest risk:** a deadline-based rerun can complete a different number of
steps under normal timing variation.  That is part of the frozen wall-clock
question, but it limits byte-for-byte outcome reproducibility.

**Cheapest falsification:** construct one core descriptor, augment its parent
copy with the seven ADR-0113 measurement fields, and require identity to pass;
then mutate each core field and the belief digest separately and require
identity to fail before any h32 policy construction.
