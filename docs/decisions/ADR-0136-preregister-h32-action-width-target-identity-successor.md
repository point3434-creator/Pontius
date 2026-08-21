# ADR-0136: Preregister the h32 action-width target-identity successor

## Status

Frozen after ADR-0135's formal failure and after observing v1's all-abstention
output, but before the single v2 h32 rerun.  This is a post-outcome mechanism
repair, not a pre-outcome strategy discovery.

## Context

ADR-0134 completed its whole workload, but its only false gate was
`target_identity`.  All four target belief SHA-256 digests and hand axes
matched ADR-0113 exactly.  Each new construction descriptor also matched the
corresponding projection of ADR-0113's descriptor exactly.

The false result came from comparing mappings with different intended stages.
The new builder returned eight or 11 immutable construction fields.  The
stored parent contained those fields plus seven later measurement fields.  A
complete-mapping equality predicate could therefore never pass.

The failed v1 output is already known: all 32 candidates violated at least one
immutable incumbent seat cap, both arms abstained on all four targets, and the
stored aggregate selected reduction was zero for each arm.  That fact is
spelled out in the machine-readable contract and is not an acceptance gate.

## Decision

Execute one additive v2 successor.  It invokes the unchanged v1 runner and v1
configuration, so the following remain byte-for-byte frozen:

- board, ranges, target shifts, incumbent, and common two-size game;
- 90-second construction-plus-planning shot clock per arm;
- 35-second complete-step reserve, eight-step ceiling, and arm order;
- warm masses, candidate stream, digest deduplication, and compact policies;
- fresh verifier construction, six-seat incumbent certification, early-stop
  order, immutable cap vector, and incumbent-wins-ties selector;
- all numerical, resource, topology, timing, and outcome-neutral v1 gates; and
- all h2 controls and h32 quality calculations.

V2 temporarily supplies the immutable v1 runner a projected parent descriptor
for its one target comparison.  No solver, evaluator, selector, candidate,
budget, or quality value is altered.  The original v1 artifact, config,
implementation, ADR-0135 decision, and ADR-0113 parent are pinned by SHA-256.

The failed v1 artifact remains failed.  V2 is a separate execution and cannot
rewrite its status.

## Corrected target-identity contract

Each target passes only when all of the following hold:

1. its target belief SHA-256 equals the matching ADR-0113 digest;
2. its hand axes are unchanged and the descriptor records that identity;
3. its construction descriptor has exactly the shift-specific field set;
4. the parent descriptor has exactly that core field set plus the seven known
   ADR-0113 measurement fields; and
5. every core value equals the exact projection of the augmented parent.

The common construction fields are shift, likelihood minimum, maximum and
mean, positive-likelihood identity, hand-axis identity, and tie rule.  Local
blocker targets additionally bind selected seat, selected hand index, selected
cards, and opponent-axis overlap.  Strength targets additionally bind the
distinct strength-level count for each seat.

The seven allowed parent-only fields are source partition, target partition,
partition ratio, the marginal total-variation vector, its mean and maximum,
and marginal measurement time.  An unknown extra parent field fails closed;
it is not silently discarded.

## Frozen successor gates

V2 passes only if:

1. the pinned v1 artifact is formally failed and its exact failed-gate set is
   `target_identity`;
2. every other v1 gate passed;
3. all four targets reproduce in the frozen order;
4. every field-set, core-projection, belief-digest, and axes check above passes;
5. the rerun reports the exact v1 config and implementation hashes;
6. the rerun passes every v1 gate, including the corrected target predicate;
7. v1 continues to report that strategy outcome is not a gate; and
8. the complete successor finishes within 3,600 seconds.

There is still no gate on candidate feasibility, abstention, step count above
one, NashConv reduction, arm winner, or strategy direction.  The known v1
outcome cannot make v2 pass or fail.

## Strategy-claim policy

The v2 top-level `strategy_quality_claim` remains null regardless of outcome.
If the mechanism passes, V2 establishes only that the repaired identity
contract and the immutable wall-clock experiment executed coherently.  Any
arm-level values remain explicitly conditional diagnostics; no action-width
ranking, equivalence claim, or production abstraction decision follows here.

This is stricter than inheriting v1's generic conditional-claim string and
preserves the user's instruction not to make a strategy-quality claim yet.

## Implementation identity

The machine-readable contract is
`experiments/configs/h32-action-width-quality-v2.json`, SHA-256
`fa372dbef73b03c9eb9ca90a687c11ee49d087d54fbf84d5afb7054cba518404`.
The additive successor is
`src/pontius/h32_action_width_quality_audit_v2.py`, SHA-256
`1978491f7439ef137705ec7feca468b75f971e23dd62301c966010d0d1f26666`.
Its direct control is
`tests/test_h32_action_width_quality_audit_v2.py`, SHA-256
`1be10c510335a77019e8ad0b9bdd6d7b935fe94c9f7b9338882657b293da0d00`.
The result target is
`experiments/results/h32-action-width-quality-v2.json`.

The direct control accepts all four exact v1 core projections.  It separately
rejects every individual core-field mutation, changed belief digest, changed
axes flag, missing field, extra construction field, and unknown parent
measurement field.  It also asserts that the known v1 outcome is disclosed
but absent from the gate mapping.

Before freeze, the complete repository passed 561 tests in `110.091 s`.  No
v2 h32 function was called; only the stored-artifact identity controls and
configuration parser executed.

## Decision branches

- **Pass:** accept the target-identity mechanism repair and retain the measured
  arms as conditional diagnostics with no top-level strategy-quality claim.
- **Identity failure:** stop; the h32 target cannot be certified against the
  parent and no third correction is authorized.
- **Any unchanged v1 gate failure:** preserve the artifact and reject this
  line rather than adjusting a deadline, tolerance, candidate, or resource
  threshold.
- **Different arm outcome:** record it exactly.  Timing-sensitive step counts
  may differ; outcome direction remains outside the gates.

## Dissent

**Confidence:** very high that the correction matches the intended immutable
target identity; high that invoking the pinned v1 runner prevents unrelated
method drift.

**Opposing evidence:** a read-only adjudication of v1 would avoid another
15-minute GPU run.  Re-execution is more conservative because the corrected
gate must coexist with every original planning and verification gate in one
clean artifact.

**Largest risk:** the outcome was observed before v2 freeze.  Explicit
disclosure and outcome-neutral gates prevent formal cherry-picking, but this is
still a repair replication rather than independent confirmatory evidence.

**Cheapest falsification:** the direct descriptor mutation matrix.  The first
h32 target then supplies the earliest runtime falsification; any identity miss
must stop its interpretation even if all stored belief hashes appear familiar.
