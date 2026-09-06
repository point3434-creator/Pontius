# One-hand event interface: brief r002

Status: proposed design; no source opening, operating authority or decision commit.
Task: v0a-event-interface-design/r002. Date: 2026-09-06. Finalizer: Codex.
Base: 5f90279ab3d7d78fe790b115a697c52262280c0d on master.
Tier C: raw event admission, continuous action timing, delivery and source admission.

## Outcome and scope

A local caller loads one portable blueprint, starts one six-player hand, sends
public events as they happen and receives the controlled seat's actions. Future
opponent actions, the complete deal and expected payouts are not interface inputs.
The caller can select its next event after observing the bot's actual response.
This is the integration interface for a later offline table host, using the
existing weak blueprint and passive fallback. It does not supply that table host.

Design one Windows binary-stdin/stdout JSON Lines tool, one hand per process,
one controlled seat and one policy loaded before the hand. Reuse the existing
event values, betting/selection/settlement implementation and action clock.
The only new runtime logic is raw-frame admission and a small ingress bridge
around the pinned runtime's dispatch shell, plus local pipe delivery.
Keep all existing production source, drivers and tests byte-identical except
the six precisely scoped registration exceptions in the companion proposal.

## Acceptance criteria

1. A real child process emits a declared non-passive table action before its
   caller supplies the next opponent event. A missing key uses the existing
   passive default; an illegal matching entry fails without an action.
2. Correctly translate all four existing event kinds. Inputs contain only the
   controlled private cards, public actions/reveals, and terminal ranks. Refuse
   extra fields, invalid types/cards, wrong ordering and terminal misuse.
   Bound the starting chip total so every derived chip output remains JSON-safe
   at the supported minimum decimal-conversion setting of 640 digits.
3. The continuous response boundary precedes UTF-8/JSON/schema admission and
   includes synchronous action-frame delivery. Preserve the inherited cutoff
   at elapsed >= 14 seconds and deadline violation at elapsed > 15 seconds.
   No clock sample is invented, latched, replayed, reset or externally supplied.
4. One action frame at most per action identity. Partial/failed writes and
   post-delivery failures remain distinguishable; no retry or false retraction.
5. Hand completion and chip results come from the runtime's settlement using
   host-supplied terminal ranks. Expose preparation, terminal bookkeeping and
   final-publication accounting at their declared cuts. Session success requires
   a successful hand result, measured full publication, complete final accounting,
   no retained fault, its fully delivered closing report and zero exit status.
   It does not certify the ranks or an independent trace.
6. Source/import admission and old-adapter compatibility pass without changing
   any src/pontius file, old driver, analyzer inference or capability grant.

## Ground truth, dependencies and limits

Ground truth is the accepted event/game/timing contracts and the independently
specified finite examples in design.md. The author chooses this correctness
population. Tests must not generate expected actions or payouts from this tool.
Use the real runtime, real pipe and independently observed action/exit outcomes.
Controlled delays or failures may operate only at the named seams under ADR-0492.

Existing dependencies: v0a.model/runtime/clock, action_clock and the portable
blueprint codec. The new tool pins private runtime dispatch-shell dependencies;
it does not read private fields of an ActionClockLedger or modify imported code.
Only this tool and a later external table host wait on this task. Operating
budget/population admission, Gate 13, analyzer repair, H32, campaign, compiled
work and training are not source-task dependencies and remain unopened.

No learned strategy, random deals, opponent policy, GUI, networking, multi-hand
session, search, strength/timing-capacity claim, new evidence reader, persistent
result owner or operating/rehearsal run. A pipe write acknowledges local byte
delivery, not application of an action by another process. No arbitrary-peer
transport liveness, OS cancellation or scheduling guarantee is made.

## Budget and stop rule

Design: one initial candidate and at most one bounded correction, each with the
two independent Tier C passes required by the workflow. Return before a third.
Proposed implementation: at most 750 production LF lines, 900 combined new-test
LF lines, two fixtures totaling 16 KiB and 120 manual registration added/removed
lines, excluding generated outputs and separate decision metadata. The larger
test allowance covers distinct admission, clock-edge, real-pipe and refusal
cases; it does not authorize a generic test/proof framework or compressed tests.
These are engineering scope bounds, not measured operating resource budgets.

One initial implementation candidate and at most one bounded correction. Stop
before exceeding scope/budget, changing sealed core, inventing clock behavior,
repairing the analyzer, adding transport cancellation or building a new proof
system. Reassess repeated residuals and WRONG SHAPE under docs/workflow.md.
Source adoption requires CLEAN reviews, the declared checks and exact commit
authorization. This commission ends at a reviewed design/source-opening proposal.
