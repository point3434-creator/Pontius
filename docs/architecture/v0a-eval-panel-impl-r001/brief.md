# Slice A brief: measured T1 export and host agreement

Checkpoint: v0a-eval-panel-impl, Slice A. Drafter/finalizer: Codex.
Reviewer: Claude, independently; Tier C also requires a second independent pass.
This round contains the implementation brief and design, not implementation.

## Authority, baseline and purpose

Implement the export bridge specified by v0a-eval-panel-design/r003 without
reopening its game, codec, policy or inference decisions. First establish what
fits and what the per-hand computation costs. Then establish that the exported
pure T1 policy produces the intended decisions through the real host.

Baseline: 46f45298a405b967976413a4b8e45e7837602316, the ceremonial adoption of
the accepted specification, parent b378104cd2934f248a9545d7d482b0db25db813c.
Its two specification documents are byte-identical to reviewed candidate
18b7527a3989f7d38830a7881c976385fe9bc4de, manifest
2664aca6f857999a4b45036b5cd3c250fbc3d8210b3132510d0e05a57e821975.
The parent specification is ../v0a-eval-panel-r001/{brief,design}.md.
The r003 disposition carries accepted implementation constraints.

Tier C: key translation and outcome classification become evidence oracles.
The protected invariant is that every reported agreement is attributable to a
completed real host decision, the declared teacher and the exact exported key;
missing records, failures and defaults cannot become successful table hits.

This draft authorizes no solver, host, test or experiment execution. It requests
review of the design. Implementation and retained runs follow their applicable
workflow gates. The accepted specification's integration to master is recorded
separately; this design is based on the identified adoption commit, not a claim
that master has advanced.

## Scope and placement

This specification round changes only this brief and its companion design.md.
Worktree: D:/Pontius-worktrees/v0a-eval-panel-impl.
Branch: codex/v0a-eval-panel-impl; baseline remains explicit at each freeze.

The first source checkpoint implements capacity and per-hand preflight only
(criteria 1-3 and their ownership/tests). Bridge completion follows the measured
decision; criteria 4-9 remain its requirements. These are ordered checkpoints
inside Slice A, not new slices or new line/review budgets.

The future Slice A implementation may create:

- src/pontius/eval_bridge.py: replayed root, compatible ranges, per-hand T1,
  deterministic export and wire-capacity calculation; no launch or journal code.
- src/pontius/eval_agreement.py: retained-outcome classification, key/reason
  reconciliation and agreement accounting; chip eligibility is a separate value.
- tools/v0a_eval_panel.py: one worker and the preflight/export/agreement phases.
- tests/test_eval_bridge.py and tests/test_eval_agreement.py, registered only
  through the existing tests/cases.json and parameterized pytest harness.
- One dated experiments script for the authorized Slice A measurement, importing
  the reusable helpers and tools; never imported by src/pontius.

The implementation also updates experiments/bot-validation.md when it issues a
retained result or changes an interpretation. Journal and generated STATUS use
the existing execution owner. No extra per-cell verification files are introduced.

Unchanged: existing codec, key and provider contracts; legal_river_continuation;
evaluation; host, session, adapter and clocks; seeded dealer; historical runners,
outputs and ADRs. Any need to change these returns for a separate scoped decision.
Slice B pairing, confidence calculations and policy rankings are out of scope.
T2, CFR export, s=6 and a new provider label are out of scope.

The inherited Slice A budget is 600 production and 400 test lines in total,
including orchestration and the dated script. Data-only plan and measurement
records are excluded. Count the whole slice, not each phase independently.
An over-budget implementation returns to the controller before freeze.

## Fixed semantics and ground truth

Use T1 against the card-blind passive villain, s=4, button 0, controlled seat 2,
blinds 1/2. Seats 0,3,4,5 fold; seat 1 completes and checks/calls. Replay the
accepted checked-to river prefix through NoLimitBettingState. At its root,
legal hero actions are CHECK and raise_to(2); there is one hero information set
per board-compatible hand. Hero hands number 1,081; each has 990 compatible
villain hands, marginalizing the folders' private cards.

The first development board is 2c 7d 9h Js Qc, ascending under the library card
encoding. The royal-spade board Ts Js Qs Ks As is a separate zero/tie correctness
control. These are Slice A diagnostics, not Slice B's four holdout strata.

Per-hand production action values come from exhaustive compatible villain
enumeration and the existing ranker/kernel settlement. The independent algorithmic
reference is evaluation.best_response on the sealed singleton-hero game, with
the villain policy explicitly assigning probability one to CALL when facing a
bet. An absent policy entry's default distribution is not that reference policy.
Teacher agreement tests export; it does not establish teacher strength or the
physical correctness of the shared poker rules.

## Acceptance and traceability

1. Capacity precedes solving. Encode real replayed keys and conservative
   CHECK/null entries using encode_blueprint. Measure wire bytes against the
   host's 1,048,576-byte input cap. Report the largest fitting prefix of the
   declared strength-blind hand permutation and its next failing prefix, if
   one exists in the 1,081-hand domain. Recheck final solved bytes independently.
   No out-of-domain overflow point or universal entry limit may be claimed.
2. Cost precedes a full pool. Measure four declared development hands separately
   with 990 villains each: As Ad, Kh Kd, Td 8d, 3c 4d. Measure the sealed
   singleton reference separately and check actions and values. Include 2c 3d
   on the royal-spade control as an exact tie. Record cold/warm context, time,
   work counts and memory where observed; distinguish measurements from estimates.
   The preflight terminates with a report and never starts a full-pool solve.
3. A full-pool launch requires a recorded decision based on that preflight and
   finite resource limits. Failure, interruption, a reference disagreement or an
   unmet prerequisite stops the phase and retains a failed/incomplete result.
   No monolithic full-range sealed game is constructed in production or tests.
4. The teacher and its pool are immutable inputs to export. Repeated export of
   identical teacher bytes is byte-identical. Decode through the existing codec;
   enumerate complete key membership and action equality for every hand in H.
   Unsupported root keys equal the complement of H within the declared board.
5. Real host agreement uses the retained hands[*].result outcome first. On a
   completed, settled, untruncated agreement hand, decode the retained child
   frames and require exactly one controlled river decision. Cross-check both
   selected action and selection_reason against teacher and independently
   replayed PreparedBlueprint.action_for. Pre-river reasons are passive_default.
   The direct BlueprintProvider.propose check is separate and also exhaustive
   over the declared root universe; neither check certifies the other.
6. The final agreement schedule covers every hand in H with a seeded, compatible
   host witness and explicitly accounts for the complement. A finite witness
   bank can yield incomplete coverage; it cannot silently redefine H. Host test
   subsets establish only their named subset. Counts reconcile to scheduled,
   completed and missing attempts without counting pre-river defaults as hits.
7. Failure precedes agreement. Rejected/unknown delivery with no decision,
   accepted action followed by failure, incomplete terminal/closure, malformed
   capture and truncation are exclusions with retained causes. Exactly-one-river
   checks apply to agreement only. A completed prefix-diverged baseline remains
   chip-eligible; no Slice A classifier may force its deletion from future Slice B.
8. Negative controls discriminate. A changed stack/prefix yields zero hits;
   an in-pool CHECK hit differs from a default by its retained reason; an off-pool
   hand defaults; reversed board input is canonicalized identically or refused.
   Report reference tie and non-tie coverage, source identity, plan identity,
   artifact wire/canonical identities, scope and unresolved observations.
9. One parent owns admission and the retained run record; one worker reuses the
   admitted host for all cells. Existing child processes inherit run context.
   Record one result and one journal line per invocation, including failure.
   Publish no per-hand admission, verification file or journal row.

Design sections 1-6 map these criteria to mechanisms and planned falsifiers.
Fresh tests must exercise real codec/provider/host boundaries where claimed.
Constructed envelope fixtures only test the classifier and are labeled as such.

## Sequence, dependencies and stopping

Review this specification cold before implementation. Keep capacity, per-hand
preflight and bridge completion within Slice A; do not import Slice B while
fixing a Slice A review. A code freeze has its own candidate and manifest.

Run authorized new/affected correctness suites on Python 3.11.15 before 3.14.6,
under the repository's disposable-snapshot procedure with -B -P, scrubbed
environment and absolute PONTIUS_GIT. Focused snapshot receipts belong to the
code freeze; broad suites follow two clean Tier C reviews. Measurements require
their separate recorded run plan and authorization. Test execution is not a
capacity, cost or agreement measurement receipt.

Stop for a demonstrated key/oracle mismatch or unexplained count: one bounded
correction within the accepted shape, then a fresh fix round with deferred
coverage. A second residual on the same contract follows the workflow's separate
candidate/root-cause rule. Conservatively count this specification round toward
the inherited two-round Slice A budget; moving from design to code does not
silently reset it. Further rounds require explicit controller reauthorization.

If no nonempty declared pool fits, stop with the measured format-fit result;
do not widen the codec. This establishes failure for this specified bridge,
not impossibility for every abstraction. If preflight is infeasible within the
authorized resources, retain the measured cost and return to the controller;
do not hide the cost by changing the game or omitting the sealed reference.
Successful export alone does not authorize a full agreement campaign.

Slice B waits for this bridge and its retained limits. The independent terminal
semantic differential does not wait. No poker-strength, equilibrium, multiway,
GPU, live-clock or four-board inference claim follows from Slice A.
