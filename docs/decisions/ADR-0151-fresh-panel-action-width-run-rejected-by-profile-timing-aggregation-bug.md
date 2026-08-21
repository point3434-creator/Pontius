# ADR-0151: Fresh-panel action-width run rejected by profile-timing aggregation bug

## Status

ADR-0150 executed once from clean commit
`a8073e5f5270f176b6144215200b6983df097d40`. The run completed all 12 printed
target blocks, then failed during aggregate gate construction with
`KeyError: 'wall_ms'`. No result artifact was written. Reject this execution
and make no strategy-quality interpretation.

## Failure

The runner correctly stores each complete widened profile as an outer row
containing `wall_ms`, GPU-pool telemetry, seat rows, and an inner `quality`
mapping. For vector exactness it intentionally assembled `quality_rows` from
the inner mappings. The `quality_ceiling` aggregation then incorrectly read
`row["wall_ms"]` from those inner mappings instead of the outer profile rows.

The exception occurred at
`src/pontius/h32_fresh_panel_action_width_warm_step_audit.py:524`, after the
console had printed all 12 frozen target identities. Because result emission
occurs after gate construction, no partial or complete JSON artifact exists.
The in-memory quality values were lost when the process exited and have not
been reconstructed, mined, or interpreted.

This is a reporter-shape bug, not evidence that a strategy, cache, exact
quality calculation, or fixed-envelope certificate failed. It nevertheless
rejects the execution because the frozen mechanism promised a complete,
machine-checkable artifact and all gates could not be assembled.

## Decision

Preserve ADR-0150, its runner, config, test, and clean execution commit
unchanged. Do not rerun ADR-0150.

Any successor must be frozen before rerun and may change only post-work
aggregation:

- assemble a separate list of outer profile rows for timing and GPU-pool
  gates;
- retain inner quality mappings for vector, zero-sum, and finiteness gates;
- include profile GPU-pool maxima in the existing 12 GB resource gate; and
- reuse ADR-0150's targets, arm order, one-step workload, policies, common
  verifier, caps, thresholds, and null strategy claim without tuning.

The correction must reject any workload, identity, outcome, threshold, or
selection change. Because the first execution left no artifact, the complete
GPU workload must be repeated once under the corrected preregistration.

## Evidential scope

The only accepted evidence from this execution is operational:

- the process launched from clean commit `a8073e5`;
- all 12 frozen target boundary messages were printed; and
- the process terminated at the identified aggregate timing lookup.

There is no accepted gate result, strategic direction, candidate selection,
action-width comparison, or strategy-quality claim.
