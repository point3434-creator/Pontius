# ADR-0116: Availability ledger is 8/8 but formally gate-failed

**Status:** Corrected v2 artifact rejected by its frozen source-status gate;
post-label availability and cost diagnostics retained without a pass claim

**Date:** 2026-08-20

## Result

The corrected ADR-0115 replay completed in 0.492 seconds and wrote
`experiments/results/h32-candidate-availability-replay-v2.json`, SHA-256
`953c42af1e0618e3055cc1c19416ab49bd9d976c3886b369a04245a3b4145cf8`.

Its top-level result is formally failed. The only false mechanism gate is
`source_status_and_gates`.

Do not report this artifact as passing and do not issue another correction
under ADR-0115. That decision explicitly forbade a second post-result repair.

## Gate localization

The v1 predicate required every source to have the literal status
`frozen_audit_executed` and `gates.passed=true`.

The three pinned sources actually report:

| Source | Status | Gates passed |
|---|---|---|
| ADR-0106 acceptance semantics | `frozen_semantics_audit_executed` | true |
| ADR-0101 candidate stream | `frozen_audit_executed` | true |
| ADR-0113 fresh transfer | `frozen_audit_executed` | true |

The first status is ADR-0106's legitimate schema value, not evidence of an
unfinished or rejected source. Its exact artifact hash was pinned before the
replay. The gate nevertheless says false as written, so the artifact fails.

Every other frozen gate passed:

- two board sources, eight targets, and 13 candidates per target;
- nested stage sizes `2,4,9,11,13`;
- full-stage selected digest identity on all eight targets;
- maximum deviation-vector sum error exactly zero;
- finite quality and cost rows;
- zero new training, evaluation, and contraction work; and
- replay time below five seconds.

This localization permits interpretation of the stored arithmetic as a
diagnostic. It does not permit changing the source-status gate after observing
the result.

## Availability diagnostic

Step two reproduced the complete step-eight selected digest on all eight
targets:

| Selected policy availability | Targets whose final policy is already available |
|---:|---:|
| iteration 0 | 5/8 |
| iteration 1 | 5/8 |
| iteration 2 | 8/8 |
| iteration 4 | 8/8 |
| iteration 8 | 8/8 |

The five iteration-zero rows are blueprint abstentions. The other three are
the two original-board local interpolations and the fresh blocker-heavy local
interpolation, all of which require current iterations one and two and no later
search state.

This was a post-label implication, not a hidden discovery: the full selected
candidate IDs were already known. The replay's contribution is mechanical
source/selector agreement and exact cost accounting.

## Recorded avoided bill

Stopping candidate construction after iteration two would avoid, across the
eight recorded targets:

- 48 warm CFR steps;
- 1,201.047 seconds of measured search;
- 530.551 seconds of complete teacher evaluation for average/current four and
  eight; and
- 1,731.598 seconds total, or 28.860 minutes.

Per target the avoided recorded bill ranges from 167.75 to 285.74 seconds.
The original-board rows used the transferred full-profile teacher; fresh rows
used the resident full-profile teacher. These historical bills are not a
cross-backend speed comparison and do not include partial-verifier savings.

## Disposition

Reject the claim that ADR-0116 passed its protocol. Retain the following weaker
engineering conclusion:

> On the complete measured two-board, eight-target h32 corpus, every final
> fixed-envelope selection is constructible by warm iteration two; iterations
> three through eight add no selected strategy value and cost 28.86 recorded
> minutes.

Use two iterations as the next systems audit's declared customer, not as an
irreversible universal stopping rule. Production architecture must retain an
anytime extension path because a wider tree, new board, or new range family can
make a later direction uniquely useful.

No rerun is warranted merely to turn the status light green. A future generic
artifact parser should validate an explicit allowed status set or, preferably,
source schema plus `gates.passed`, but that maintenance change must not be used
to relabel this artifact.

## Next decision

The evidence now justifies integrating resident terminal contraction into the
CFR traverser and measuring exactly one and two warm steps from frozen h32
states. ADR-0113 measured training plus warm search at 87.98% of wall; the
existing resident evaluator already proves the underlying contraction exact to
about `2.5e-15` and cuts verification materially. The next audit should test
whether that mechanism accelerates regret reads and preserves one-step solver
state, not run another expensive board first.
