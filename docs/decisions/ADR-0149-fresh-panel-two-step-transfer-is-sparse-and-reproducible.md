# ADR-0149: Fresh-panel two-step transfer is sparse and reproducible

## Status

ADR-0148 executed from clean preregistration commit
`322569dc4e24904a291896ad69639e04712c8e7e`.  All 25 corrected and unchanged
frozen gates passed.

## Evidence identity

The 953,292-byte result artifact is
`experiments/results/h32-fresh-panel-target-transfer-v2.json`, SHA-256
`62f0c3807c158f3507f6d1280a187bfd50b37df28e23b7a51feb4e523e697f0b`.
The corrected run completed in `1163.3311 s` and records strict clean Git state.

Windows enterprise Code Integrity briefly blocked CuPy before the recorded
invocation.  That attempt stopped before runtime measurement, target
construction, or a search step and wrote no artifact.  The recorded invocation
began only after CuPy 14.2.0, CUDA runtime 13.2, and driver 13.3 imported through
the frozen approved environment.

## Corrected warm-start result

All twelve exact post-warm policy digests differed from their source-policy
digests, confirming that the rejected v1 gate was categorically wrong rather
than a one-target anomaly.  The numerical discrepancies were negligible:

- maximum probability error: `2.220446049250313e-16`;
- maximum mean information-set total variation: `3.436885724709844e-17`.

These are over four thousand times and almost three thousand times below the
respective `1e-12` and `1e-13` gates.  Every other ADR-0146 gate remained
unchanged.

## Transfer outcome

One of twelve targets selected a non-blueprint candidate.  Panel 2 balanced
under `local_blocker_seat3_x2` selected warm `search_current2`.

- Blueprint normalized NashConv: `0.00260953203188428`.
- Selected normalized reduction: `0.00014533124323137`.
- Raw NashConv reduction: `0.0043599372969411`.
- Feasible non-blueprint candidates: five of six.
- Tightest selected cap margin: `0.0001637196` raw inside the cap.

Every seat's deviation gain decreased.  The six raw changes ranged from
`-0.0013080` to `-0.0001637`, so the selection is not a guard-band accident.

The other eleven targets abstained to their immutable source blueprints.  The
local-blocker acceptance rate is therefore one of six; all six dense-strength
targets abstained.  Across three deterministic boards and two range families,
two-step transfer is real but sparse.

## Reproduction of the rejected run

The corrected run independently reproduced the same selected candidate ID on
all twelve targets, including `search_current2` on the single positive target.
Candidate policy digests were not bit-identical across GPU runs, consistent
with the known reduction-order behavior of this lineage.  The maximum
candidate normalized-quality difference between runs was only
`8.85e-17`.  Reproduction is therefore numerical and decision-level, not a
false claim of cross-run byte identity.

## Exactness and resources

The run executed 24 target search steps, 12 blueprint profiles, and 72 complete
candidate profiles.  All source, target, checkpoint, restore, finite, zero-sum,
vector-accounting, interpolation, cap, certificate, count, and resource gates
passed.

- Maximum search step: `11,892.0519 ms`.
- Maximum complete profile: `12,740.2580 ms`.
- Maximum resident-cache compile: `4,759.2619 ms`.
- Maximum target workspace compile: `82.7391 ms`.
- Maximum GPU-pool total: `7,706,509,312` bytes.
- Maximum zero-sum residual: `8.826e-15`.

The complete repository suite passed 583 tests in `143.647 s` under the frozen
GPU environment after the run.

## Certificate and scope

Every selected or abstained policy remains inside an independent one-shot
certificate anchored to its immutable source `average64` blueprint.  A
selection never becomes a new anchor, and the certificate expires after one
public transition.  No cumulative episode-safety or coalition claim is made.

The audit constructed zero two-size trees.  Its action-width quality claim is
null.

## Decision

Accept the corrected one-size transfer measurement.  Retain the two-step
resident candidate ladder as a real but low-recall local adapter, with exact
blueprint-relative six-seat acceptance.

Do not infer a population acceptance rate from three boards, do not weaken the
fixed envelope to raise recall, and do not treat dense all-seat shifts as a
successful customer.  The next strategic expansion should be separately
preregistered and must not reuse this outcome as an action-width gate.
