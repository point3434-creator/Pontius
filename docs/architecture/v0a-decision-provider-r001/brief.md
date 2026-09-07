# Selectable decision provider: design brief

Date: 2026-09-06. Task: v0a-decision-provider-design. Finalizer: Codex.
Base: e205cd8cd6f46a50db8b2d0cb1f39366da0f2767.
Status: proposed architecture; no source changes, adoption, or launch authority.
Tier C: policy identity, hidden-information admission, timing and action receipts.

## Controller request and outcome

The controller approved starting a replaceable decision module with a simple
baseline, keeping complete-bot functionality ahead of training and strength work.
The intended deliverable is a session using a selected strategy whose actions
depend on its visible situation. An empty blueprint remains available as fallback.
This design covers that complete path; a library-only result is not completion.

## Acceptance criteria

1. A caller can select the existing blueprint behavior or the fixed baseline.
   Baseline decisions exercise folds, calls and legal raises across fresh finite
   correctness situations, including preflop and postflop decisions.
2. Provider inputs contain only owned immutable visible-state values, legal
   actions and a non-authoritative remaining-work estimate. No dealer reference,
   opponent hole cards, future board, schedule seed, result or engine handle.
3. The engine validates context and action, owns the clock and delivery, retains
   provider identity and outcome, and uses the admitted fallback on ordinary
   provider failure. Clock, context, identity and delivery failures remain fatal.
4. A provider result never becomes a fictitious blueprint hit or certificate.
   Versioned records distinguish proposed action, applied action and fallback.
5. A real child-process session exercises the selected provider, rotates the
   button, carries stacks, settles the game and produces complete honest output.
6. Historical source and retained attempts are preserved. Any current-file
   supersession is enumerated and separately adopted before implementation.

## Ground truth, seams and dependencies

Game legality and settlement come from the existing betting kernel and independently
calculated finite examples. Baseline choices come from the author's explicit rules
in design.md; they are engineering specifications, not optimal-poker oracles.
Boundary faults and clock schedules follow docs/workflow.md's controlled-failure
conditions, exercising the real decision and transport paths.

Seams: visible event admission; legal decision construction; provider selection;
engine validation and fallback; continuous action wall; mailbox delivery; decision
serialization; host receipt verification; source admission; session rendering.
Only this selectable-strategy session depends on the change. Neural inference,
training, self-play, league management and strength analysis remain separate work.

## Scope and proportionality

This task produces a design and two independent cold reviews. It does not modify
production, tests, accepted decisions, STATUS or source-admission pins. The source
opening must bind exact base blobs, paths, schemas, implementation budget and finite
test controls after the controller reviews this design.

Prefer a small provider package plus narrow integration changes to duplicating the
1,200-line runtime or the host stack. That requires explicit prospective exceptions
for current source versions; sealed historical blobs and artifacts stay immutable.
If the controller declines those exceptions, return for a different design.

Design budget: one initial candidate and one bounded correction, two independent
Tier C reviews per substantive round; return before a third round. No general
plugin system, arbitrary imports, worker pool, training loop or new evidence owner.
Proposed implementation ceiling: 1,200 added/removed production lines and 1,800
added test lines, excluding generated registration output. Exceeding it requires
rescoping before implementation grows. These are engineering limits, not measured
operating budgets. No strength, timing-capacity or hard process-cancellation claim.
