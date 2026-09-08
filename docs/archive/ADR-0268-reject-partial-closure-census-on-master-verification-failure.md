# ADR-0268: Reject partial closure census on master verification failure

- Status: accepted process correction; ADR-0267 census result rejected
- Date: 2026-08-22
- Implements: ADR-0267
- Clean preregistration commit: `f35ee5113df2643563b4865d41305c7c37baaea6`
- Result artifact: none written

## Invocation outcome

The single authorized ADR-0267 invocation began from the clean preregistration
commit and preserved the frozen 42-target order. Five target-level progress
summaries printed. During target 6, the sparse behavioral master raised
`ArithmeticError: behavioral master primal/dual verification failed`. The
process exited nonzero before final gate assembly and wrote no result artifact.

Reject the invocation as a census result. Do not infer a 5-of-42 closure rate,
do not omit the failing context, and do not rerun under ADR-0267.

## Partial-label boundary

The printed retrospective optimizer summaries are:

| Target | Cut rounds | State | Seconds |
|---|---:|---|---:|
| `panel_1/balanced/checks_then_bet_seat0` | 3 | verified closure | 15.147 |
| `panel_1/blocker_heavy/checks_then_bet_seat1` | 2 | verified closure | 11.563 |
| `panel_2/blocker_heavy/checks_then_bet_seat2` | 0 | verified closure | 12.766 |
| `panel_2/balanced/checks_then_bet_seat3` | 1 | verified closure | 14.115 |
| `panel_3/balanced/checks_then_bet_seat4` | — | no-new-facet numerical stall | 12.975 |

Target 6 was
`panel_3/blocker_heavy/checks_then_bet_seat5`, acting seat 4. It reached a
master solve before failure; whether an earlier iteration opened an in-memory
oracle label is not recoverable from the absent artifact. Treat its entire
retrospective optimization state as opened by the failed invocation.

All six contexts already had prior strategy evidence, so this incident does
not consume a fresh holdout or change roster eligibility. It does prohibit
describing a correction as wholly label-blind.

## What is already identified

Universal one-round closure on the retained corpus is falsified independently
of the process failure: the first two fixed targets require three and two
multi-cut rounds. The full convex mechanism closes those two programs, but the
current one-round live engine is not a globally closed optimizer on every
retained context.

The fifth target also validates ADR-0267's distinction between facet closure
and certified program closure. No genuinely new response row remained, yet
exact cap feasibility and/or `U - L` did not close. Without the discarded
in-memory row, the binding component is unknown; classify it only as the
frozen numerical-stall branch.

These facts retain their target-specific meaning because they were printed
before the unrelated target-6 exception. They are not a complete census,
population estimate, or license to tune a threshold.

## Process defect

The runner treated a target-local verified-master exception as a campaign-wide
exception. It therefore discarded valid preceding rows and prevented the
remaining fixed roster from becoming right-censored observations. That is an
orchestration defect, not evidence against the convex theorem or exact safety
certificate.

A correction must:

- preserve the identical 42-target order, tolerances, cuts, resource caps, and
  scientific decision table;
- catch and classify target-local numerical failures without treating them as
  closure;
- release the failed target's resident GPU state before continuing;
- checkpoint completed target rows so a later process failure cannot erase
  them;
- disclose recomputation of the first five opened summaries and target 6;
- leave a failed target explicitly censored in the final distribution; and
- continue to exclude every post-fold identity and emit only the blueprint.

Adding a diagnostic replay of the failing LP is permitted only as a
non-authoritative process row. It may not loosen the master tolerance, accept a
failed KKT gate, replace exact cap feasibility, or create a candidate.

## Decision

Seal this rejection before editing the runner. Preregister a target-isolated
v2 census with durable per-target checkpoints. Run no target again until the
new implementation, control, hashes, partial-label disclosure, and stopping
semantics are committed from a clean tree.
